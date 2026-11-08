import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import mongomock
import pytest
from pydantic import ValidationError
from pymongo.errors import AutoReconnect

from app.core.security import hash_password, verify_password
from app.db.mongo_migration import (
    MigrationSnapshot,
    SnapshotMembership,
    SnapshotUser,
    import_snapshot,
    read_snapshot,
    source_content_digest,
    verify_snapshot,
    write_snapshot,
)
from app.db.mongo_probe import make_probe_document
from app.db.mongo_store import MongoStore
from app.domain.uml.models import ProjectDocument


@pytest.fixture
def snapshot() -> MigrationSnapshot:
    now = datetime(2026, 11, 6, 20, 0, 0, 123456, tzinfo=UTC)
    password_hash = hash_password("migration-test-password")
    owner = SnapshotUser(
        id=uuid4(),
        email="owner@example.com",
        password_hash=password_hash,
        created_at=now,
        updated_at=now,
    )
    editor = owner.model_copy(update={"id": uuid4(), "email": "editor@example.com"})
    document = make_probe_document().model_copy(update={"owner_id": owner.id})
    legacy = ProjectDocument(ownerId=uuid4(), metadata={"name": "Legacy unassigned"})
    return MigrationSnapshot(
        users=[owner, editor],
        projects=[document, legacy],
        memberships=[
            SnapshotMembership(project_id=document.id, user_id=editor.id, role="EDITOR"),
        ],
    )


@pytest.fixture
def store() -> MongoStore:
    return MongoStore(mongomock.MongoClient()["migration_unit"])


def test_backup_round_trip_preserves_document_and_rejects_tampering(
    snapshot: MigrationSnapshot,
    tmp_path: Path,
) -> None:
    path = tmp_path / "snapshot.json"
    write_snapshot(snapshot, path)
    assert read_snapshot(path) == snapshot
    data = json.loads(path.read_text(encoding="utf-8"))
    data["snapshot"]["projects"][0]["metadata"]["tampered"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        read_snapshot(path)


def test_existing_backup_is_never_overwritten(snapshot: MigrationSnapshot, tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    write_snapshot(snapshot, path)
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_snapshot(snapshot, path)
    assert path.read_bytes() == original


def test_import_preserves_ids_hashes_permissions_layout_and_legacy_ownership(
    snapshot: MigrationSnapshot,
    store: MongoStore,
) -> None:
    result = import_snapshot(snapshot, store)
    assert result == {
        "users": 2,
        "projects": 2,
        "memberships": 1,
        "legacyOwnerProjects": 1,
        "inserted": 4,
    }
    owner = snapshot.users[0]
    migrated = store.get_user_by_id(owner.id)
    assert migrated["password_hash"] == owner.password_hash
    assert verify_password("migration-test-password", migrated["password_hash"])
    assert store.get_project(snapshot.projects[0].id) == snapshot.projects[0]
    assert store.get_project(snapshot.projects[1].id).owner_id == snapshot.projects[1].owner_id
    assert store.get_user_by_id(snapshot.projects[1].owner_id) is None
    assert store.get_membership(snapshot.projects[0].id, snapshot.users[1].id) == "EDITOR"
    assert import_snapshot(snapshot, store)["inserted"] == 0
    assert verify_snapshot(snapshot, store)["projects"] == 2


def test_conflicting_project_aborts_before_inserting_users(
    snapshot: MigrationSnapshot,
    store: MongoStore,
) -> None:
    document = snapshot.projects[0].model_copy(update={"revision": 999})
    store.create_project(document)
    with pytest.raises(ValueError, match="different data"):
        import_snapshot(snapshot, store)
    assert store.users.count_documents({}) == 0
    assert store.get_project(document.id).revision == 999


def test_conflicting_email_does_not_merge_distinct_accounts(
    snapshot: MigrationSnapshot,
    store: MongoStore,
) -> None:
    existing = store.create_user(snapshot.users[0].email, "different-hash")
    with pytest.raises(ValueError, match="another identity"):
        import_snapshot(snapshot, store)
    assert store.users.count_documents({}) == 1
    assert store.projects.count_documents({}) == 0
    assert store.get_user_by_email(snapshot.users[0].email)["_id"] == existing["_id"]


def test_interrupted_import_can_resume_without_overwriting_users(
    snapshot: MigrationSnapshot,
    store: MongoStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_insert = store.projects.insert_one

    def fail(*args: object, **kwargs: object):
        raise AutoReconnect("simulated connection loss")

    monkeypatch.setattr(store.projects, "insert_one", fail)
    with pytest.raises(AutoReconnect):
        import_snapshot(snapshot, store)
    assert store.users.count_documents({}) == 2
    monkeypatch.setattr(store.projects, "insert_one", original_insert)
    assert import_snapshot(snapshot, store)["inserted"] == 2
    assert verify_snapshot(snapshot, store)["memberships"] == 1


def test_snapshot_rejects_memberships_with_missing_users(snapshot: MigrationSnapshot) -> None:
    data = snapshot.model_dump(mode="json")
    data["memberships"][0]["user_id"] = str(uuid4())
    with pytest.raises(ValidationError):
        MigrationSnapshot.model_validate(data)


def test_source_change_detection_ignores_export_time_but_not_project_changes(
    snapshot: MigrationSnapshot,
) -> None:
    later = snapshot.model_copy(update={"exported_at": snapshot.exported_at + timedelta(minutes=1)})
    assert source_content_digest(later) == source_content_digest(snapshot)
    later = snapshot.model_copy(deep=True)
    later.projects[0].metadata["new"] = "change"
    assert source_content_digest(later) != source_content_digest(snapshot)

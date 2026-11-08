"""CU-25: read-only SQL snapshots and non-overwriting, restartable Mongo imports."""

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field, ValidationError, model_validator
from pymongo.errors import DuplicateKeyError, PyMongoError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.memberships import ProjectMembershipRecord, ProjectRole
from app.db.mongo_connection import MongoConnectionSettings, create_mongo_client
from app.db.mongo_projects import project_to_mongo
from app.db.mongo_store import MongoStore
from app.db.projects import ProjectRecord, project_document_from_record
from app.db.users import UserRecord
from app.domain.uml.models import DomainModel, ProjectDocument


class SnapshotUser(DomainModel):
    id: UUID
    email: str
    password_hash: str = Field(min_length=1, repr=False)
    created_at: datetime
    updated_at: datetime

    def mongo_document(self) -> dict:
        return {
            "_id": str(self.id),
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SnapshotMembership(DomainModel):
    project_id: UUID
    user_id: UUID
    role: ProjectRole


class MigrationSnapshot(DomainModel):
    schema_version: Literal[1] = 1
    exported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    users: list[SnapshotUser]
    projects: list[ProjectDocument]
    memberships: list[SnapshotMembership]

    @model_validator(mode="after")
    def validate_integrity(self):
        user_ids = {user.id for user in self.users}
        emails = {user.email for user in self.users}
        project_ids = {project.id for project in self.projects}
        if len(user_ids) != len(self.users) or len(emails) != len(self.users):
            raise ValueError("Duplicate user identity or email in snapshot")
        if any(user.email != user.email.strip().lower() for user in self.users):
            raise ValueError("Source email is not normalized; no implicit rewrite is permitted")
        if len(project_ids) != len(self.projects):
            raise ValueError("Duplicate project identity in snapshot")
        pairs = {(row.project_id, row.user_id) for row in self.memberships}
        if len(pairs) != len(self.memberships):
            raise ValueError("Duplicate membership in snapshot")
        owners = {project.id: project.owner_id for project in self.projects}
        for row in self.memberships:
            if row.project_id not in project_ids or row.user_id not in user_ids:
                raise ValueError("Membership references a missing project or user")
            if owners[row.project_id] == row.user_id:
                raise ValueError("Owner cannot have an additional membership")
        return self

    def summary(self) -> dict[str, int]:
        user_ids = {user.id for user in self.users}
        return {
            "users": len(self.users),
            "projects": len(self.projects),
            "memberships": len(self.memberships),
            "legacyOwnerProjects": sum(
                project.owner_id not in user_ids for project in self.projects
            ),
        }

    def project_documents(self) -> list[dict]:
        memberships: dict[UUID, dict[str, str]] = {}
        for row in self.memberships:
            memberships.setdefault(row.project_id, {})[str(row.user_id)] = row.role.value
        result = []
        for project in self.projects:
            data = project_to_mongo(project)
            data["_memberships"] = memberships.get(project.id, {})
            result.append(data)
        return result


def canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def snapshot_digest(snapshot: MigrationSnapshot) -> str:
    return hashlib.sha256(
        canonical_bytes(snapshot.model_dump(mode="json", by_alias=True))
    ).hexdigest()


def source_content_digest(snapshot: MigrationSnapshot) -> str:
    payload = snapshot.model_dump(mode="json", by_alias=True)
    payload.pop("exported_at")
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def export_sql_snapshot(session_factory=None) -> MigrationSnapshot:
    if session_factory is None:
        from app.db.session import SessionLocal

        session_factory = SessionLocal

    with session_factory() as session:
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        users = [
            SnapshotUser(
                id=row.id,
                email=row.email,
                password_hash=row.password_hash,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in session.scalars(select(UserRecord).order_by(UserRecord.id))
        ]
        projects = [
            project_document_from_record(row)
            for row in session.scalars(select(ProjectRecord).order_by(ProjectRecord.id))
        ]
        memberships = [
            SnapshotMembership(project_id=row.project_id, user_id=row.user_id, role=row.role)
            for row in session.scalars(
                select(ProjectMembershipRecord).order_by(
                    ProjectMembershipRecord.project_id,
                    ProjectMembershipRecord.user_id,
                )
            )
        ]
        return MigrationSnapshot(users=users, projects=projects, memberships=memberships)


def write_snapshot(snapshot: MigrationSnapshot, path: Path) -> None:
    envelope = {
        "sha256": snapshot_digest(snapshot),
        "snapshot": snapshot.model_dump(
            mode="json",
            by_alias=True,
        ),
    }
    # Exclusive creation protects previous backups. The CLI only permits the
    # ignored artifacts/cu25 directory, never a tracked project file.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(canonical_bytes(envelope))
        output.flush()
        os.fsync(output.fileno())
    if snapshot_digest(read_snapshot(path)) != snapshot_digest(snapshot):
        raise ValueError("Backup verification failed")


def read_snapshot(path: Path) -> MigrationSnapshot:
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if set(envelope) != {"sha256", "snapshot"}:
        raise ValueError("Invalid backup envelope")
    snapshot = MigrationSnapshot.model_validate(envelope["snapshot"])
    if envelope["sha256"] != snapshot_digest(snapshot):
        raise ValueError("Snapshot checksum does not match")
    return snapshot


def _equal_document(collection, expected: dict) -> bool:
    existing = collection.find_one({"_id": expected["_id"]})
    if existing is not None and existing != expected:
        raise ValueError("Destination contains different data; no overwrite was performed")
    return existing is not None


def import_snapshot(snapshot: MigrationSnapshot, store: MongoStore) -> dict[str, int]:
    expected_users = [user.mongo_document() for user in snapshot.users]
    expected_projects = snapshot.project_documents()
    # Preflight every record before the first insert; preserve unrelated data.
    for data in expected_users:
        _equal_document(store.users, data)
        by_email = store.users.find_one({"email": data["email"]})
        if by_email is not None and by_email["_id"] != data["_id"]:
            raise ValueError("Destination email belongs to another identity")
    for data in expected_projects:
        _equal_document(store.projects, data)
    store.ensure_indexes()
    inserted = 0
    for collection, records in ((store.users, expected_users), (store.projects, expected_projects)):
        for data in records:
            if _equal_document(collection, data):
                continue
            try:
                collection.insert_one(data)
                inserted += 1
            except DuplicateKeyError:
                # A concurrent identical import is safe. Never overwrite a
                # conflicting destination after a failed/partial import.
                if not _equal_document(collection, data):
                    raise
    verify_snapshot(snapshot, store)
    return {**snapshot.summary(), "inserted": inserted}


def verify_snapshot(snapshot: MigrationSnapshot, store: MongoStore) -> dict[str, int]:
    for user in snapshot.users:
        if not _equal_document(store.users, user.mongo_document()):
            raise ValueError("Migrated user is missing")
    for project in snapshot.project_documents():
        if not _equal_document(store.projects, project):
            raise ValueError("Migrated project is missing")
    return snapshot.summary()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CU-25: preserve SQL data while migrating to Mongo"
    )
    parser.add_argument("action", choices=["export", "inspect", "import", "verify", "source-check"])
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument(
        "--prefix", default="", help="Optional isolated cu25_<UUID>_ rehearsal prefix"
    )
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[3]
    backup_root = (workspace / "artifacts" / "cu25").resolve()
    backup_path = args.backup.resolve()
    if (
        not backup_root.is_relative_to(workspace)
        or not backup_path.is_relative_to(backup_root)
        or backup_path.suffix != ".json"
    ):
        print("FAIL: backups must be JSON files within artifacts/cu25, outside Git.")
        return 2
    try:
        if args.action == "export":
            snapshot = export_sql_snapshot()
            write_snapshot(snapshot, backup_path)
            result = snapshot.summary()
        else:
            snapshot = read_snapshot(backup_path)
            if args.action == "source-check":
                if source_content_digest(snapshot) != source_content_digest(export_sql_snapshot()):
                    raise ValueError("SQL changed after export; cutover must not proceed")
                result = snapshot.summary()
            elif args.action == "inspect":
                result = snapshot.summary()
            else:
                config = MongoConnectionSettings()
                with create_mongo_client(config) as client:
                    store = MongoStore(
                        client[config.mongodb_database], collection_prefix=args.prefix
                    )
                    result = (
                        import_snapshot(snapshot, store)
                        if args.action == "import"
                        else verify_snapshot(snapshot, store)
                    )
        print(json.dumps({"status": "PASS", "action": args.action, **result}))
    except (OSError, ValueError, KeyError, ValidationError, SQLAlchemyError, PyMongoError):
        # Backup payloads contain credential hashes and personal data. Do not
        # print exceptions, records, email addresses, URI or passwords.
        print("FAIL: migration validation or storage access failed. Source data was not changed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

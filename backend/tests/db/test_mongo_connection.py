from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pymongo.errors import ConnectionFailure, DuplicateKeyError

from app.db import mongo_connection, mongo_probe
from app.db.mongo_connection import MongoSettings
from app.db.mongo_projects import project_from_mongo, project_to_mongo


def settings(**overrides: object) -> MongoSettings:
    values = {
        "mongodb_uri": "mongodb://user:secret@localhost:27017",
        "mongodb_database": "unit_cu25_probe",
    }
    values.update(overrides)
    return MongoSettings(_env_file=None, **values)


def test_configuration_does_not_expose_the_connection_secret() -> None:
    config = settings()
    assert "secret" not in repr(config)
    assert "secret" not in config.model_dump_json()


@pytest.mark.parametrize("database", ["production", "", "other.db_cu25_probe", "_cu25_probe"])
def test_probe_requires_an_explicit_isolated_database(database: str) -> None:
    with pytest.raises(ValidationError):
        settings(mongodb_database=database)


@pytest.mark.parametrize("timeout", [0, 99, 30001])
def test_connection_has_bounded_timeouts(timeout: int) -> None:
    with pytest.raises(ValidationError):
        settings(mongodb_timeout_ms=timeout)


def test_connection_uses_acknowledged_primary_reads_and_majority_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = MagicMock()
    monkeypatch.setattr(mongo_connection, "MongoClient", factory)
    mongo_connection.create_mongo_client(settings())
    options = factory.call_args.kwargs
    assert options["w"] == "majority"
    assert options["readConcernLevel"] == "majority"
    assert options["readPreference"] == "primary"
    assert options["connect"] is False
    assert options["timeoutMS"] == 15000


def test_probe_without_settings_exits_without_contacting_storage(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing_config() -> MongoSettings:
        return MongoSettings(_env_file=None, mongodb_uri="", mongodb_database="")

    factory = MagicMock()
    monkeypatch.setattr(mongo_probe, "MongoSettings", missing_config)
    monkeypatch.setattr(mongo_probe, "create_mongo_client", factory)
    assert mongo_probe.main() == 2
    factory.assert_not_called()
    assert "NOT RUN" in capsys.readouterr().out


def test_probe_failure_does_not_print_driver_credentials_or_claim_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(mongo_probe, "MongoSettings", settings)
    factory = MagicMock(side_effect=ConnectionFailure("mongodb://user:secret@private-host"))
    monkeypatch.setattr(mongo_probe, "create_mongo_client", factory)
    assert mongo_probe.main() == 1
    output = capsys.readouterr().out
    assert "FAIL" in output
    assert "secret" not in output
    assert "private-host" not in output
    assert "PASS" not in output


def test_probe_does_not_delete_a_document_if_its_insert_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    collection = client.__getitem__.return_value.__getitem__.return_value
    collection.write_concern.acknowledged = True
    collection.insert_one.side_effect = DuplicateKeyError("existing identity")
    monkeypatch.setattr(mongo_probe, "create_mongo_client", lambda _: client)
    with pytest.raises(DuplicateKeyError):
        mongo_probe.run_probe(settings())
    collection.delete_one.assert_not_called()


def test_probe_cleans_up_its_own_document_after_a_failed_round_trip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    collection = client.__getitem__.return_value.__getitem__.return_value
    collection.write_concern.acknowledged = True
    collection.find_one.return_value = None
    monkeypatch.setattr(mongo_probe, "create_mongo_client", lambda _: client)
    with pytest.raises(RuntimeError, match="round-trip"):
        mongo_probe.run_probe(settings())
    inserted = collection.insert_one.call_args.args[0]
    collection.delete_one.assert_called_once_with({"_id": inserted["_id"]})
    client.drop_database.assert_not_called()
    collection.drop.assert_not_called()


def test_live_probe_fixture_preserves_a_nonempty_diagram() -> None:
    document = mongo_probe.make_probe_document()
    restored = project_from_mongo(project_to_mongo(document))
    assert restored == document
    assert [element.kind for element in restored.uml_model.elements] == [
        "class",
        "class",
        "association",
    ]
    assert restored.uml_model.elements[0].attributes[0].name == "nombre"
    assert len(restored.diagram_layout.nodes) == 2


@pytest.mark.parametrize("accepted_names", [set(), {"ConcurrentA", "ConcurrentB"}])
def test_concurrent_probe_rejects_zero_or_two_winners(
    monkeypatch: pytest.MonkeyPatch, accepted_names: set[str]
) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    store = MagicMock()
    store.update_if_revision.side_effect = lambda document, _: (
        document.uml_model.elements[-1].name in accepted_names
    )
    monkeypatch.setattr(mongo_probe, "create_mongo_client", lambda _: client)
    monkeypatch.setattr(mongo_probe, "MongoProjectStore", lambda _: store)
    with pytest.raises(RuntimeError, match="exactly one winner"):
        mongo_probe.concurrent_update_probe(
            settings(), "test_probe", mongo_probe.make_probe_document()
        )


def test_concurrent_probe_uses_two_clients_and_returns_the_accepted_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def client_factory(_: MongoSettings) -> MagicMock:
        client = MagicMock()
        client.__enter__.return_value = client
        return client

    factory = MagicMock(side_effect=client_factory)
    store = MagicMock()
    store.update_if_revision.side_effect = lambda document, _: (
        document.uml_model.elements[-1].name == "ConcurrentB"
    )
    monkeypatch.setattr(mongo_probe, "create_mongo_client", factory)
    monkeypatch.setattr(mongo_probe, "MongoProjectStore", lambda _: store)
    document = mongo_probe.make_probe_document()
    winner = mongo_probe.concurrent_update_probe(settings(), "test_probe", document)
    assert factory.call_count == 2
    assert store.update_if_revision.call_count == 2
    assert winner.uml_model.elements[-1].name == "ConcurrentB"
    assert winner.revision == document.revision + 1
    assert document.revision == 0

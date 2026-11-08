from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import unquote, urlsplit

import pytest
from dotenv import dotenv_values
from pymongo.errors import OperationFailure

from app.db import mongo_configure


def test_configuration_preserves_existing_sql_and_encodes_password(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("# Existing settings\nDATABASE_URL=keep-sql\nJWT_SECRET_KEY=keep-jwt\n")
    password = "p@ss:/#${other}"
    mongo_configure.save_probe_connection(
        env_path, "cluster.example.mongodb.net", "probe", password
    )
    values = dotenv_values(env_path)
    assert values["DATABASE_URL"] == "keep-sql"
    assert values["JWT_SECRET_KEY"] == "keep-jwt"
    uri = urlsplit(values["MONGODB_URI"])
    assert unquote(uri.password) == password
    assert values["MONGODB_DATABASE"] == "examen_sw1_cu25_probe"
    assert "# Existing settings" in env_path.read_text()
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.parametrize("host", ["mongodb+srv://cluster.mongodb.net", "outside.example", "x\ny"])
def test_invalid_hostname_does_not_modify_existing_environment(tmp_path: Path, host: str) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("DATABASE_URL=unchanged\n")
    with pytest.raises(ValueError):
        mongo_configure.save_probe_connection(env_path, host, "probe", "password")
    assert env_path.read_text() == "DATABASE_URL=unchanged\n"


def test_replace_failure_preserves_original_and_removes_staged_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("DATABASE_URL=unchanged\n")

    def denied(*_: object) -> None:
        raise PermissionError("simulated failure")

    monkeypatch.setattr(mongo_configure.os, "replace", denied)
    with pytest.raises(PermissionError):
        mongo_configure.save_probe_connection(env_path, "cluster.mongodb.net", "probe", "password")
    assert env_path.read_text() == "DATABASE_URL=unchanged\n"
    assert list(tmp_path.glob("*.tmp")) == []


def test_noninteractive_configuration_refuses_to_read_a_visible_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mongo_configure.sys, "argv", ["configure", "--host", "cluster.mongodb.net"])
    monkeypatch.setattr(mongo_configure.sys.stdin, "isatty", lambda: False)

    def must_not_prompt(*_: object) -> str:
        raise AssertionError("Password prompt must not run without a terminal")

    monkeypatch.setattr(mongo_configure.getpass, "getpass", must_not_prompt)
    assert mongo_configure.main() == 2


def test_rejected_cloud_password_does_not_replace_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("DATABASE_URL=unchanged\n")
    factory = MagicMock(side_effect=OperationFailure("bad auth : authentication failed", 8000))
    monkeypatch.setattr(mongo_configure, "create_mongo_client", factory)
    with pytest.raises(OperationFailure):
        mongo_configure.save_probe_connection(
            env_path, "cluster.mongodb.net", "probe", "wrong", verify=True
        )
    assert env_path.read_text() == "DATABASE_URL=unchanged\n"
    assert list(tmp_path.glob("*.tmp")) == []


def test_verified_configuration_authenticates_before_saving(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    monkeypatch.setattr(mongo_configure, "create_mongo_client", lambda _: client)
    env_path = tmp_path / ".env"
    mongo_configure.save_probe_connection(
        env_path, "cluster.mongodb.net", "probe", "saved-password", verify=True
    )
    client.admin.command.assert_called_once_with("ping")
    assert dotenv_values(env_path)["MONGODB_DATABASE"] == "examen_sw1_cu25_probe"


def test_interactive_retry_does_not_expose_rejected_credentials(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        mongo_configure.sys, "argv", ["configure", "--host", "cluster.mongodb.net", "--verify"]
    )
    monkeypatch.setattr(mongo_configure.sys.stdin, "isatty", lambda: True)
    password = MagicMock(side_effect=["wrong-secret", "correct-secret"])
    save = MagicMock(
        side_effect=[OperationFailure("bad auth : authentication failed; wrong-secret", 8000), None]
    )
    monkeypatch.setattr(mongo_configure.getpass, "getpass", password)
    monkeypatch.setattr(mongo_configure, "save_probe_connection", save)
    assert mongo_configure.main() == 0
    assert save.call_count == 2
    output = capsys.readouterr().out
    assert "wrong-secret" not in output
    assert "correct-secret" not in output
    assert "saved" in output

"""Save a probe credential locally without putting its password in chat/argv."""

import argparse
import getpass
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

from dotenv import set_key
from pymongo.errors import OperationFailure, PyMongoError

from app.db.mongo_connection import MongoSettings, create_mongo_client


def save_probe_connection(
    env_path: Path, host: str, username: str, password: str, *, verify: bool = False
) -> None:
    if not re.fullmatch(r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.mongodb\.net", host):
        raise ValueError("Use the Atlas hostname, without a URI, path or credentials")
    if not username or not password:
        raise ValueError("A database username and password are required")
    uri = (
        f"mongodb+srv://{quote(username, safe='')}:{quote(password, safe='')}@{host}/"
        "?retryWrites=true&w=majority&appName=cu25-probe"
    )
    database = "examen_sw1_cu25_probe"
    config = MongoSettings(_env_file=None, mongodb_uri=uri, mongodb_database=database)
    if verify:
        with create_mongo_client(config) as client:
            client.admin.command("ping")
    original = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    # Stage beside .env so replacement is atomic, preserving the old file if a
    # write fails. Never print either the existing environment or the new URI.
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=env_path.parent, suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            output.write(original)
        set_key(temporary, "MONGODB_URI", uri, quote_mode="always")
        set_key(temporary, "MONGODB_DATABASE", database, quote_mode="always")
        os.replace(temporary, env_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure only the CU-25 Atlas probe")
    parser.add_argument("--host", required=True, help="Atlas hostname, without credentials")
    parser.add_argument("--user", default="cu25_probe")
    parser.add_argument(
        "--verify", action="store_true", help="Check Atlas authentication before saving"
    )
    args = parser.parse_args()
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not sys.stdin.isatty():
        print("Run this command in your own interactive terminal; password input must stay hidden.")
        return 2
    try:
        for _ in range(3):
            password = getpass.getpass(
                "Password for cu25_probe (hidden; no letters or asterisks appear): "
            )
            try:
                save_probe_connection(env_path, args.host, args.user, password, verify=args.verify)
            except OperationFailure as error:
                message = str(error).lower()
                if args.verify and ("authentication failed" in message or "bad auth" in message):
                    print("Atlas rejected this password. Use the database user's saved password.")
                    continue
                raise
            break
        else:
            print("Configuration not saved after three rejected attempts.")
            return 1
    except (KeyboardInterrupt, EOFError):
        print("Cancelled; configuration was not saved.")
        return 2
    except (OSError, ValueError, PyMongoError):
        print("Configuration not saved. Check hostname, credential and local file access.")
        return 1
    print("Probe configuration saved in backend/.env. Existing SQL settings are preserved.")
    print("Next: python -m app.db.mongo_probe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

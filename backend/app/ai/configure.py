"""Interactive local secret entry; never accept a key in command-line arguments."""

import re
from getpass import getpass
from pathlib import Path


def save_key(path: Path, key: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,200}", key):
        raise ValueError("Invalid key format; no configuration was changed")
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = r"(?m)^GEMINI_API_KEY\s*=.*$"
    entry = "GEMINI_API_KEY=" + key
    if re.search(pattern, previous):
        updated = re.sub(pattern, entry, previous)
    else:
        updated = previous.rstrip("\r\n") + "\n" + entry + "\n"
    path.write_text(updated, encoding="utf-8")


def main():
    path = Path(__file__).resolve().parents[2] / ".env"
    print("Create your key personally at https://aistudio.google.com/api-keys")
    print("No billing or account changes are made by this script.")
    key = getpass("Gemini API key (hidden; never paste it into chat): ").strip()
    save_key(path, key)
    print("Key saved privately in backend/.env. Existing settings are preserved.")
    print("The real provider benchmark still needs to be run.")


if __name__ == "__main__":
    main()

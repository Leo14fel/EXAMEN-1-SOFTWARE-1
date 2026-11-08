import pytest

from app.ai.configure import save_key


def test_key_entry_preserves_settings_and_replaces_existing_key(tmp_path):
    path = tmp_path / ".env"
    path.write_text("DATABASE_URL=preserved\nGEMINI_API_KEY=old\nOTHER=ok\n", encoding="utf-8")
    save_key(path, "x" * 30)
    assert (
        path.read_text(encoding="utf-8")
        == "DATABASE_URL=preserved\nGEMINI_API_KEY=" + "x" * 30 + "\nOTHER=ok\n"
    )
    save_key(path, "y" * 30)
    assert path.read_text(encoding="utf-8").count("GEMINI_API_KEY=") == 1


def test_key_entry_rejects_newline_injection_without_touching_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("KEEP=ok", encoding="utf-8")
    with pytest.raises(ValueError):
        save_key(path, "x" * 30 + "\nINJECTED=true")
    assert path.read_text(encoding="utf-8") == "KEEP=ok"

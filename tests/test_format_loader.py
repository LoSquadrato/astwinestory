import json
import tempfile
from pathlib import Path
import pytest

from core.formats.format_loader import load_format, FormatLoaderError, FORMATS_DIR


def test_load_known_format():
    fmt = load_format("SugarCube")
    assert fmt.name == "SugarCube"


def test_missing_format_raises(tmp_path):
    with pytest.raises(FormatLoaderError) as exc:
        load_format("nonexistentformat")
    assert "Format definition not found" in str(exc.value)


def test_invalid_json(tmp_path, monkeypatch):
    # create a temp file with bad json and point loader to it via monkeypatch
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json }")
    # monkeypatch resolution helper to return our bad file
    def fake_resolve(name):
        return str(bad)
    monkeypatch.setattr("core.formats.format_loader._resolve_path", fake_resolve)
    with pytest.raises(FormatLoaderError) as exc:
        load_format("anything")
    assert "Invalid JSON" in str(exc.value)

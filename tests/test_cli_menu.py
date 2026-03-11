import pytest
from core.cli.menus import MenuOption, display_menu, select_from_menu


def test_menu_selection_simple(monkeypatch, capsys):
    options = [MenuOption(key="a", label="Option A"), MenuOption(key="b", label="Option B")]
    # simulate user entering '1'
    monkeypatch.setattr('builtins.input', lambda prompt='': '1')
    selected = select_from_menu("Choose", options)
    captured = capsys.readouterr()
    assert "Option A" in captured.out
    assert selected.key == "a"


def test_menu_invalid_then_valid(monkeypatch, capsys):
    inputs = iter(["x", "3", "2"])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
    selected = select_from_menu("Choose", [MenuOption(key="x", label="X"), MenuOption(key="y", label="Y")])
    out = capsys.readouterr().out
    assert "Invalid input" in out
    assert selected.key == "y"


def test_get_format_list(tmp_path):
    # create fake format files
    d = tmp_path / "formats"
    d.mkdir()
    (d / "foo.json").write_text("{}"); (d / "bar.json").write_text("{}")
    sub = d / "sub"
    sub.mkdir()
    (sub / "baz.json").write_text("{}")
    from core.cli.menus import get_format_list
    results = get_format_list(d, format_list=[])
    keys = {opt.key for opt in results}
    assert keys == {"foo", "bar", "baz"}


def test_suggest_and_confirm(tmp_path, monkeypatch):
    from core.cli.run_repl import _suggest_output_path, _confirm_output_path
    source = tmp_path / "story.twee"
    source.write_text("hello")
    sug = _suggest_output_path(source, "foo")
    assert sug.name == "story_foo.twee"
    # confirm default
    monkeypatch.setattr('builtins.input', lambda prompt='': '')
    assert _confirm_output_path(sug) == sug
    # custom path relative
    monkeypatch.setattr('builtins.input', lambda prompt='': 'custom.tw')
    out = _confirm_output_path(sug)
    assert out.name == 'custom.tw' and out.parent == source.parent
    # absolute custom path
    abs_path = tmp_path / 'other.tw'
    monkeypatch.setattr('builtins.input', lambda prompt='': str(abs_path))
    assert _confirm_output_path(sug) == abs_path

from cli.menus import MenuOption, select_from_menu, get_format_list


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
    results = get_format_list(d, format_list=[])
    keys = {opt.key for opt in results}
    assert keys == {"foo", "bar", "baz"}
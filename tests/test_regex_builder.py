import pytest
import re
from core.formats.format_loader import load_format, FormatLoaderError, _build_definition
from core.parser.regex_builder import RegexBuilder


def test_available_keys_for_sugarcube():
    fmt = load_format("SugarCube")
    rb = RegexBuilder(fmt)
    keys = rb.available()
    # expect at least these
    combined = rb.build_combined_pattern(keys)
    assert isinstance(combined, re.Pattern)
    # try matching a macro syntax
    assert combined.search("<<print 1>>")


def test_empty_format_has_no_patterns():
    empty_syntax = {
        "name": "Empty",
        "version": "1",
        "syntaxtype": "",
        "variables": {"global_prefix": "", "local_prefix": ""},
        "links": {"open": "", "close": ""}       
    }
    fmt = _build_definition(empty_syntax)
    rb = RegexBuilder(fmt)
    assert rb.available() == []
    assert rb.build_combined_pattern(["variable", "link", "macro"]) is None
    assert isinstance(rb.build_title_pattern(), re.Pattern)
    assert rb.get("variable") is None

def test_empty_format_raises_error():
    with pytest.raises(FormatLoaderError):
        _build_definition({"name": "Empty", "version": "1", "variables": None, "links": None})
        
def test_combined_pattern_builder():
    fmt = load_format("SugarCube")
    rb = RegexBuilder(fmt)
    combined = rb.build_combined_pattern(["variable", "link", "macro"])
    assert combined is not None
    # test matching a variable
    assert combined.search("$variable")
    # test matching a link
    assert combined.search("[[Link]]")
    # test matching a macro
    assert combined.search("<<print 1>>")
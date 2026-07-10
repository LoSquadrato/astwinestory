import pytest
import re
from core.formats.format_loader import load_format, FormatLoaderError, _build_definition
from core.src.regex_builder import RegexBuilder


def test_available_keys_for_sugarcube():
    fmt = load_format("SugarCube")
    rb = RegexBuilder(fmt)
    keys = rb.available()
    # expect at least these
    combined = rb.build_pattern(keys)
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
    assert rb.build_pattern(["variable", "link", "macro"]) is None
    assert isinstance(rb.build_title_pattern(), re.Pattern)
    assert rb.get("variable") is None

def test_empty_format_raises_error():
    with pytest.raises(FormatLoaderError):
        _build_definition({"name": "Empty", "version": "1", "variables": None, "links": None})
        
def test_combined_pattern_builder():
    fmt = load_format("SugarCube")
    rb = RegexBuilder(fmt)
    combined = rb.build_pattern(["variable", "link", "macro"])
    assert combined is not None
    # test matching a variable
    assert combined.search("$variable")
    # test matching a link
    assert combined.search("[[Link]]")
    # test matching a macro
    assert combined.search("<<print 1>>")
    
def test_meta_pattern_builder():
    fmt = load_format("SugarCube")
    rb = RegexBuilder(fmt)
    meta_pattern = rb.build_pattern(["meta"])
    assert meta_pattern is not None
    # test matching a meta syntax
    match = meta_pattern.search("[widget myWidget]")
    assert match is not None
    assert match.group("meta") == "[widget myWidget]"
    assert match.group("meta_prefix") == "["
    assert match.group("meta_content") == "widget myWidget"
    assert match.group("meta_suffix") == "]"
    match = meta_pattern.search("{meta content}")
    assert match is not None
    assert match.group("meta") == "{meta content}"
    assert match.group("meta_prefix") == "{"
    assert match.group("meta_content") == "meta content"
    assert match.group("meta_suffix") == "}"
    
def test_content_pattern_builder():
    fmt = load_format("SugarCube")
    rb = RegexBuilder(fmt)
    content_pattern = rb.build_node_content_pattern()
    assert content_pattern is not None
    # test matching a variable
    assert content_pattern.search("$variable")
    # test matching a link
    assert content_pattern.search("[[Link]]")
    # test matching a macro
    assert content_pattern.search("<<print 1>>")
    
def test_passage_content_pattern_builder():
    fmt = load_format("SugarCube")
    rb = RegexBuilder(fmt)
    passage_content_pattern = rb.build_passage_content_pattern()
    assert passage_content_pattern is not None
    # test matching a variable
    assert passage_content_pattern.search("$variable")
    # test matching a link
    assert passage_content_pattern.search("[[Link]]")
    # test matching a macro
    assert passage_content_pattern.search("<<print 1>>")
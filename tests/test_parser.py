import pytest
import re

from core.formats.format_loader import load_format
from core.parser.content_parser import Parser, ParsingError
from core.ast import TextNode, MacroNode, LinkNode, VariableNode, OperatorNode, MetaNode


def test_basic_text_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = ":: Greeting!!!\nHello world"
    passages = Parser.split_passage(text)
    assert len(passages) == 1
    passage = parser.parse_passage(passages[0])
    assert passage.name == "Greeting!!!"
    assert len(passage.children) == 1
    node = passage.children[0]
    assert isinstance(node, TextNode)
    assert node.value.strip() == text.strip()

def test_special_passage_parsing():
    fmt = load_format("SugarCube")
    # add a special passage name for testing
    parser = Parser(fmt)
    text = ":: Start\nThis is a special passage."
    passages = Parser.split_passage(text)
    assert len(passages) == 1
    passage = parser.parse_passage(passages[0])
    assert passage.name == "Start"
    assert len(passage.children) == 1
    node = passage.children[0]
    assert isinstance(node, TextNode)
    assert node.value.strip() == text.strip()

def test_macro_and_link_children():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    sample = ":: P\nSee <<print 1+1>> and [[go|Here]] now."
    passage = parser.parse_passage(sample)
    # expect Text, Macro, Text, Link, Text
    types = [type(n) for n in passage.children]
    assert types[0] is TextNode
    assert types[1] is MacroNode
    assert types[2] is TextNode
    assert types[3] is LinkNode
    assert types[4] is TextNode
    assert passage.children[3].display == "go"
    assert passage.children[3].children[0].value == "Here"
    assert passage.children[1].macro_type == "print"
    # check that macro content is parsed as Text + Operator + Text
    types = [type(n) for n in passage.children[1].children]
    assert any(isinstance(c, TextNode) for c in passage.children[1].children)
    assert any(isinstance(c, OperatorNode) for c in passage.children[1].children)


def test_variable_node_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    nodes = parser.parse_content(
        "before $hero after", 
        parser._patterns.build_macro_inner_pattern()
        )
    assert any(isinstance(node, VariableNode) for node in nodes)
    variable = next(node for node in nodes if isinstance(node, VariableNode))
    assert variable.name == "$hero"
    assert variable.scope == "global"


def test_operator_node_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    nodes = parser.parse_content(
        "a + b",
        parser._patterns.build_macro_inner_pattern()
        )
    assert any(isinstance(node, OperatorNode) for node in nodes)
    operator = next(node for node in nodes if isinstance(node, OperatorNode))
    assert operator.operator == "+"


def test_meta_node_building():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    meta_match = re.match(r"(?P<meta_raw><<widget myWidget>>)", "<<widget myWidget>>")
    assert meta_match is not None
    node = parser._build_node("meta", meta_match)
    assert isinstance(node, MetaNode)
    assert node.raw == "<<widget myWidget>>"


def test_pattern_missing_format_raises():
    # create minimal format lacking any patternable fields
    minimal = load_format("SugarCube").model_copy()
    # clear every source used by build_macro_inner_pattern
    minimal.variables.global_prefix = ""
    minimal.variables.local_prefix = ""
    minimal.macros = None
    minimal.links = None
    minimal.operators = {}
    minimal.literals = {}
    minimal.formatting = {}
    parser = Parser(minimal)
    with pytest.raises(ParsingError):
        parser.parse_content("foo", parser._patterns.build_macro_inner_pattern())

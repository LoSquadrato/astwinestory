import pytest
import re

from core.formats.format_loader import load_format
from core.parser.content_parser import Parser, ParsingError
from core.ast import TextNode, MacroNode, LinkNode, VariableNode, OperatorNode, MetaNode

def test_parse_passage_basic():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = ":: Greeting!!!\nHello world"
    passage = parser.parse_passage(text)
    assert passage.name == "Greeting!!!"
    assert len(passage.children) == 1
    node = passage.children[0]
    assert isinstance(node, TextNode)
    assert node.value.strip() == text.split("\n", 1)[1].strip()

def test_parse_passage_with_metadata():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = ":: Greeting!!! [tag1 tag2] {meta}\nHello world"
    passage = parser.parse_passage(text)
    assert passage.name == "Greeting!!!"
    assert passage.tags == "tag1 tag2"
    assert passage.metadata == "meta"
    

def test_basic_text_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = ":: Greeting!!!\nHello world"
    passages = Parser.split_passage(text)
    assert len(passages) == 1
    passage = parser.parse_passage(text)
    assert passage.name == "Greeting!!!"
    assert len(passage.children) == 1
    node = passage.children[0]
    assert isinstance(node, TextNode)
    assert node.value.strip() == text.split("\n", 1)[1].strip()

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
    assert node.value.strip() == text.split("\n", 1)[1].strip()

def test_extract_macro_content():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = "<<if $x=5 in y>> content here<<endif>>"
    content = parser.extract_macro_content(text, 0)
    match = parser.get_macro_match(content)
    assert match is not None
    assert match.group("macro_type") == "if"
    assert content.strip() == "<<if $x=5 in y>>"
    assert match.end() == len(content)

def test_link_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = ":: Passage\nGo to [[Next Passage]] now."
    passage = parser.parse_passage(text)
    assert len(passage.children) == 3
    assert isinstance(passage.children[1], LinkNode)
    link = passage.children[1]
    assert len(link.children) == 1
    assert isinstance(link.children[0], TextNode)
    assert link.children[0].value.strip() == "Next Passage"
    
def test_link_with_display_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = ":: Passage\nGo to [[Next Passage|Here]] now."
    passage = parser.parse_passage(text)
    assert len(passage.children) == 3
    assert isinstance(passage.children[1], LinkNode)
    link = passage.children[1]
    assert link.display == "Next Passage"
    assert len(link.children) == 1
    assert isinstance(link.children[0], TextNode)
    assert link.children[0].value.strip() == "Here"

def test_macro_parsing_without_children_and_text():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = ":: P\nTwo is <<print 1+1>> is two."
    passage = parser.parse_passage(text)
    assert len(passage.children) == 3
    assert isinstance(passage.children[1], MacroNode)
    macro = passage.children[1]
    assert macro.macro_type == "print"
    assert len(macro.children) == 3
    assert isinstance(macro.children[0], TextNode)
    assert macro.children[0].value.strip() == "1"
    assert isinstance(macro.children[1], OperatorNode)
    assert macro.children[1].operator.strip() == "+"
    assert isinstance(macro.children[2], TextNode)
    assert macro.children[2].value.strip() == "1"

def test_macro_parsing_with_text():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = "Two is <<print 1+1>> and three is <<print 1+2>>."
    nodes = parser.parse_content(text, parser._patterns.build_combined_pattern(["macro"]))
    assert len(nodes) == 5
    assert isinstance(nodes[0], TextNode)
    assert nodes[0].value.strip() == "Two is"
    assert isinstance(nodes[1], MacroNode)      
    assert nodes[1].macro_type == "print"
    assert len(nodes[1].children) == 3
    assert isinstance(nodes[1].children[0], TextNode)
    assert nodes[1].children[0].value.strip() == "1"
    assert isinstance(nodes[1].children[1], OperatorNode)
    assert nodes[1].children[1].operator.strip() == "+"
    assert isinstance(nodes[1].children[2], TextNode)
    assert nodes[1].children[2].value.strip() == "1"
    assert isinstance(nodes[2], TextNode)
    assert nodes[2].value.strip() == "and three is"
    assert isinstance(nodes[3], MacroNode)
    assert nodes[3].macro_type == "print"
    assert len(nodes[3].children) == 3
    assert isinstance(nodes[3].children[0], TextNode)
    assert nodes[3].children[0].value.strip() == "1"
    assert isinstance(nodes[3].children[1], OperatorNode)
    assert nodes[3].children[1].operator.strip() == "+"
    assert isinstance(nodes[3].children[2], TextNode)
    assert nodes[3].children[2].value.strip() == "2"
    assert isinstance(nodes[4], TextNode)
    assert nodes[4].value.strip() == "."

def test_matching_node_type():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    pattern = parser._patterns.build_combined_pattern(["variable", "link", "macro", "meta"])
    kind1 = parser.matching_node_type(pattern.search("<<print 1>>"))
    kind2 = parser.matching_node_type(pattern.search("[[Link]]"))
    kind3 = parser.matching_node_type(pattern.search("$variable"))
    kind4 = parser.matching_node_type(pattern.search("<meta>"))
    assert kind1 == "macro"
    assert kind2 == "link"
    assert kind3 == "variable"
    assert kind4 == "meta"
    
    
def test_iterate_content():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = "before <<print 1>> after [[Link]] and $variable"
    pattern = parser._patterns.build_combined_pattern(["macro", "link", "variable"])
    matches = list(parser.iterate_content(text, pattern))
    assert len(matches) == 3
    assert matches[0][0] == "macro"
    assert matches[1][0] == "link"
    assert matches[2][0] == "variable"
    

def test_parse_macro_content():
    # helper for testing macro content extraction
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    text = "before <<print 1+1>> after"
    pattern = parser._patterns.build_combined_pattern(["macro"])
    nodes = parser.parse_content(text, pattern)
    assert len(nodes) == 3
    assert isinstance(nodes[0], TextNode)
    assert nodes[0].value.strip() == "before"
    assert isinstance(nodes[1], MacroNode)
    assert nodes[1].macro_type == "print"
    assert len(nodes[1].children) == 3
    assert isinstance(nodes[1].children[0], TextNode)
    assert nodes[1].children[0].value.strip() == "1"
    assert isinstance(nodes[1].children[1], OperatorNode)
    assert nodes[1].children[1].operator.strip() == "+"
    assert isinstance(nodes[1].children[2], TextNode)
    assert nodes[1].children[2].value.strip() == "1"    

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
        parser._patterns.build_content_pattern()
        )
    assert any(isinstance(node, VariableNode) for node in nodes)
    variable = next(node for node in nodes if isinstance(node, VariableNode))
    assert variable.name == "hero"
    assert variable.scope == "global_prefix"


def test_operator_node_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    nodes = parser.parse_content(
        "a + b",
        parser._patterns.build_content_pattern()
        )
    assert isinstance(nodes[0], TextNode)
    assert isinstance(nodes[1], OperatorNode)
    assert isinstance(nodes[2], TextNode)
    assert nodes[1].operator == "+"

def test_and_or_operator_parsing():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    nodes = parser.parse_content(
        "a and b or c",
        parser._patterns.build_content_pattern()
        )
    operators = [node.operator for node in nodes if isinstance(node, OperatorNode)]
    assert "and" in operators
    assert "or" in operators

def test_meta_node_building():
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    meta_node = parser.parse_content("<meta content>", parser._patterns.build_combined_pattern(["meta"]))
    assert len(meta_node) == 1
    assert isinstance(meta_node[0], MetaNode)


def test_pattern_missing_format_raises():
    # create minimal format lacking any patternable fields
    minimal = load_format("SugarCube").model_copy()
    # clear every source used by build_content_pattern
    minimal.variables.global_prefix = ""
    minimal.variables.local_prefix = ""
    minimal.macros = None
    minimal.links = None
    minimal.operators = {}
    minimal.literals = {}
    minimal.formatting = {}
    parser = Parser(minimal)
    with pytest.raises(ParsingError):
        parser.parse_content("foo", None)

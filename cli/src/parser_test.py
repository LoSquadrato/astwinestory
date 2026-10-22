import pytest
from .parser import Parser, PASSAGE_CONTENT_KEYS
from .format_definition import load_format
from .node import MacroNode, TextNode, HookNode, MetaNode


def test_macro_with_quote():
    text = '(go-to: "16 More Ways to Kill a Vampire")'
    format = load_format("harlowe")
    parser = Parser(format, [text])
    nodes = parser.parse_content(text, parser.build_pattern(["macro", "quote"]))
    assert nodes is not None
    assert isinstance(nodes[0], MacroNode)
    assert nodes[0].children is not None
    assert isinstance(nodes[0].children[0], TextNode)
    assert nodes[0].children[0].value == "16 More Ways to Kill a Vampire"
    
def test_mixed_content():
    pass
    text = '(click: ?three)[(set: $option to 3)(go-to: "16 More Ways to Kill a Vampire")] (elseif: $sequence is 4)[(if: $option is 1)[Maggie whirls around. I blink and her |knives>[knives] are in her hands.(click: ?knives)'
    format = load_format("harlowe")
    parser = Parser(format, [text])
    nodes = parser.parse_content(text, parser.build_pattern(["macro", "quote", "text"]))
    assert nodes is not None
    assert isinstance(nodes[0], MacroNode)
    
def test_macro_with_hook():
    text = '(click: ?one)[(go-to: "16 More Ways to Kill a Vampire")]'
    format = load_format("harlowe")
    parser = Parser(format, [text])
    nodes = parser.parse_content(text, parser.build_pattern(PASSAGE_CONTENT_KEYS))
    nodes = parser.group_by_linear_nodes(nodes)
    assert nodes is not None
    assert isinstance(nodes[0], MacroNode)
    assert nodes[0].hook is not None
    assert isinstance(nodes[0].hook, HookNode)
    assert nodes[0].hook.children is not None
    assert isinstance(nodes[0].hook.children[0], MacroNode)
    
def test_macro_with_hook_nested_meta():
    text = '''(elseif: $sequence is 4)[(if: $option is 1)[Maggie whirls around. I blink and her |knives>[knives] are in her hands.(click: ?knives)[

//Maggie's knives are named John and Mina. She's a romantic.//]

She slashes the vampire across the throat, and then stabs up, skewering her heart!

The vampire's last expression is one of |surprise>[surprise] as she poofs into dust.(click: ?surprise)[

//She's probably impressed and honored that Maggie just killed her exactly like Quincey Morris and Jonathan Harker killed Dracula.//] ](elseif: $option is 2)[Luke brings his modified nail gun up to bear.

He shoots the vampire full of nails as she falls.

One in the naval, |chest>[one in each eye], two in the neck, a bunch in the chest.(click: ?chest)[

Luke is a stupid good shot.]

Maggie yanks me out of the way, but the vampire is turning to dust even as she hits the ground where I was standing.](elseif: $option is 3)[For some reason, Maggie has a |poker>[burning red poker.](click: ?poker)[

//I don't ask Maggie about these things.//]

She turns it up and braces it so that the vampire lands on it.

The hot iron burns through the vampire's chest like a blowtorch through butter.

She makes an awful gurgling noise as her lungs are pureed, and then turns to dust.]

(set: $sequence to 5)
[[Next vampire.->16 More Ways to Kill a Vampire]] ]
    '''
    format = load_format("harlowe")
    parser = Parser(format, [text])
    nodes = parser.parse_content(text, parser.build_pattern(PASSAGE_CONTENT_KEYS))
    nodes = parser.group_by_linear_nodes(nodes)
    assert nodes is not None
    assert isinstance(nodes[0], MacroNode)
    assert nodes[0].hook is not None
    assert isinstance(nodes[0].hook, HookNode)
    
    
def test_nested_meta():
    text = '[Maggie whirls around. I blink and her |knives>[knives] are in her hands.]'
    format = load_format("harlowe")
    parser = Parser(format, [text])
    nodes = parser.parse_content(text, parser.build_pattern(PASSAGE_CONTENT_KEYS))
    nodes = parser.group_by_linear_nodes(nodes)
    assert nodes is not None
    assert isinstance(nodes[0], MetaNode) or isinstance(nodes[0], MetaNode)
    assert MetaNode in [type(node) for node in nodes]
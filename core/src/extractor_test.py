from core.src.extractor import Extractor
from core.src.regex_builder import RegexBuilder
from core.formats import load_format

#########################################################
# Extractor tests for markup syntax
#########################################################
def test_extract_markup_macro_content():
    fmt = load_format("SugarCube")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "<<if $x=5 in y>> content here<</if>>"
    content = extractor.get_macro_params_markup(text)
    assert content["offset"] == len(text)
    assert content["kind"] == "macro"
    assert content["macro_type"] == "if"
    assert content["children"] == "$x=5 in y"
    assert content["hook"] == " content here"

def test_extract_markup_simple_macro():
    fmt = load_format("SugarCube")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "<<print 1+1>>"
    content = extractor.get_macro_params_markup(text)
    assert content["offset"] == len(text)
    assert content["kind"] == "macro"
    assert content["macro_type"] == "print"
    assert content["children"] == "1+1"
    
def test_extract_markup_nested_macro():
    fmt = load_format("SugarCube")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "<<if $x>0>> <<print $x>> <</if>>"
    content = extractor.get_macro_params_markup(text)
    assert content["offset"] == len(text)
    assert content["kind"] == "macro"
    assert content["macro_type"] == "if"
    assert content["children"] == "$x>0"
    assert content["hook"] == " <<print $x>> "
    
##########################################################
# Extractor tests for linear syntax
##########################################################  
    
def test_extract_linear_macro_with_hook():
    fmt = load_format("Harlowe")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "(font: \"Courier New\")[This is a hook.]"
    content = extractor.get_macro_params_linear(text)
    print(content)
    print(f"macro: {len(content['macro_type'])}; children: {len(content['children'])}; hook: {len(content['hook'])}")
    assert content["offset"] == len(text)
    assert content["kind"] == "macro"
    assert content["macro_type"] == "font:"
    assert content["children"] == " \"Courier New\""
    assert content["hook"] == "This is a hook."
    
def test_extract_linear_macro_with_control_nested_hook():
    fmt = load_format("Harlowe")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "(if: not $lostTheSword)[(set: $weapon to \"a holy sword\")](else: )[(set:$weapon to \"an unholy swear-word\")]"
    content = extractor.get_macro_params_linear(text)
    print(content)
    assert content["offset"] == len(text)
    assert content["kind"] == "macro"
    assert content["macro_type"] == "if:"
    assert content["children"] == " not $lostTheSword"
    assert content["hook"] == "(set: $weapon to \"a holy sword\")](else: )[(set:$weapon to \"an unholy swear-word\")"
    
def test_extract_linear_nested_plain_macro():
    fmt = load_format("Harlowe")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "(set: $lostTheSword to (either:true,false))"
    content = extractor.get_macro_params_linear(text)
    print(content)
    assert content["offset"] == len(text)
    assert content["kind"] == "macro"
    assert content["macro_type"] == "set:"
    assert content["children"] == " $lostTheSword to (either:true,false)"

def test_extract_linear_hook():
    fmt = load_format("Harlowe")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "[This is a hook.]"
    content = extractor._extract_linear_content_stack(text, extractor._patterns.build_hook_content_pattern(), 0)
    assert content == "[This is a hook.]"
    
def test_extract_first_macro_match():
    fmt = load_format("Harlowe")
    extractor = Extractor(fmt, RegexBuilder(fmt))
    text = "(set: $lostTheSword to (either:true,false))"
    match = extractor._get_macro_first_match(text)
    macro_type = match.group("opener").strip(fmt.macros.open)
    assert match is not None
    assert match.group("opener") == "(set:"
    assert macro_type == "set:"
    
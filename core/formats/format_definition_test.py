from core.formats.format_definition import FormatDefinition
from core.formats.format_loader import load_format

def test_is_control_macro_opener():
    fmt = load_format("Harlowe")
    assert fmt.is_control_macro_opener("if:") is True
    assert fmt.is_control_macro_opener("else:") is False
    assert fmt.is_control_macro_opener("elseif:") is False
    assert fmt.is_control_macro_opener("print:") is False
    
def test_is_control_macro_continue():
    fmt = load_format("Harlowe")
    assert fmt.is_control_macro_continue("if:") is False
    assert fmt.is_control_macro_continue("else:") is True
    assert fmt.is_control_macro_continue("elseif:") is True
    assert fmt.is_control_macro_continue("print:") is False
    
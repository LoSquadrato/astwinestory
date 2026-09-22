import json
import os
from src.utils import FORMATS_PATH
from pydantic import BaseModel, ValidationError as PydanticValidationError


class FormatDefinitionError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "FormatDefinitionError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        

class VariableDefinition(BaseModel):
    global_prefix: str        # '$'
    local_prefix:  str        # '_'

class MacroDefinition(BaseModel):
    open:       str                 # '<<' | '('
    close:      str                 # '>>' | ')'
    close_tag:  str = ""
    hook_open:  str = ""     # '[' for linear syntax, None for markup syntax
    hook_close: str = ""     # ']' for linear syntax, None for markup syntax
    hooked:      dict[str, list[str]] = {}
    plain:      dict[str, list[str]] = {}
    
class HtmlDefinition(BaseModel):
    open:  str = "<"
    close: str = ">"
    close_tag: str = "/"
    html_tags: list[str] = []
    
class LinkDefinition(BaseModel):
    open:             str       # '[['
    close:            str       # ']]'
    separators:       list[str] = []    # '->', '<-', '|'

# todo: add func to check key in assets jSON and populate field in format definition, so the JSON schema 
# work like a template for format definition, regex builder and content parser.
# Check if we can maintain the pydantic mapping or we need to create a func to convert JSON to FormatDefinition instance,
# which also validate the format definition and raise error if invalid.
class FormatDefinition(BaseModel):
    
    name:             str
    version:          str
    syntaxtype:       str
    variables:        VariableDefinition 
    links:            LinkDefinition
    macros:           MacroDefinition | None = None
    operators:        dict[str, list[str]] = {}
    literals:         dict[str, list[str]] = {}
    formatting:       dict[str, list[str]] = {}
    meta:             dict[str, list[str]] = {}
    html:             HtmlDefinition | None = None
    special_passages: list[str]            = []


    def is_variable(self, token: str) -> bool:
        if not self.variables:
            raise ValueError("FormatDefinition.variables is not defined")
        return (token.startswith(self.variables.global_prefix) or
                token.startswith(self.variables.local_prefix))

    
    def have_hook(self, macro_type: str) -> bool:
        if not self.macros or not self.macros.hooked:
            raise ValueError("FormatDefinition.macros.hooked is not defined")
        for lst in self.macros.hooked.values():
            if macro_type in lst:
                return True
        return False
    
    def is_special_passage(self, token: str) -> bool:
        if not self.special_passages:
            raise ValueError("FormatDefinition.special_passages is not defined")
        return token in self.special_passages   
     
    
    def get_meta_tokens(self, token: str) -> list[str]:
        if not self.meta:
            raise ValueError("FormatDefinition.meta is not defined")
        for tokens in self.meta.values():
            if token in tokens and len(tokens) == 2:
                return tokens
        return []
    
    def is_control_macro_opener(self, macro_type: str) -> bool:
        hooked = self.get_hooked_macros()
        if "control_opener" in hooked and macro_type in hooked["control_opener"]:
            return True
        return False
    
    def is_control_macro_continue(self, macro_type: str) -> bool:
        hooked = self.get_hooked_macros()
        if "control_continue" in hooked and macro_type in hooked["control_continue"]:
            return True
        return False
    
    def get_syntaxtype(self) -> str:
        if not self.syntaxtype:
            raise ValueError("FormatDefinition.syntaxtype is not defined")
        return self.syntaxtype
    
    def get_hooked_macros(self) -> dict[str, list[str]]:
        if not self.macros or not self.macros.hooked:
            raise ValueError("FormatDefinition.macros.hooked is not defined")
        return self.macros.hooked
    
    # Get the subtype key for a given token based on its kind.
    def get_token_subtype(self, field: str, token: str) -> tuple[str, int] | None:
        if not token or not field:
            return None
        match field:
            case "operator", "literal", "formatting", "meta":
                if not hasattr(self, field) or not self.__dict__[field]:
                    return None
                for k, v in self.__dict__[field].items():
                    if token in v:
                        return (k, v.index(token))
            case "macro":
                if not self.macros or not self.macros.plain or not self.macros.hooked:
                    return None
                for k, v in self.macros.plain.items():
                    if token in v:
                        return ("plain."+ k, v.index(token))
                for k, v in self.macros.hooked.items():
                    if token in v:
                        return ("hooked."+ k, v.index(token))
            case _:
                return None
  
# Format loading utilities
    
def load_format(format_name: str) -> FormatDefinition:
    path = _resolve_path(format_name)
    if not path:
        raise FormatDefinitionError([f"Format definition not found for '{format_name}'."])
    raw  = _read_json(path)
    return _build_definition(raw)


def _resolve_path(format_name: str) -> str:
    normalized = format_name.lower().replace(" ", "_")
    
    candidates = [os.path.join(FORMATS_PATH, f"{normalized}.json")]

    for path in candidates:
        if os.path.isfile(path):
            return path
        
    return ""


def _read_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FormatDefinitionError([f"Invalid JSON in format definition '{path}': {e}"])
    except OSError as e:
        raise FormatDefinitionError([f"Failed to read format definition '{path}': {e}"])


def _build_definition(raw: dict) -> FormatDefinition:
    try:
        return FormatDefinition.model_validate(raw)
    except PydanticValidationError as e:
        raise FormatDefinitionError([f"Invalid format definition: {e}"]) from e
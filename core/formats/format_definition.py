from pydantic import BaseModel, ConfigDict, model_validator
from typing import Any


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
    inner:      dict[str, list[str]] = {}
    
    
class LinkDefinition(BaseModel):
    open:             str       # '[['
    close:            str       # ']]'
    separators:       list[str] = []    # '->', '<-', '|'

# todo: add func to check key in assets jSON and populate field in format definition, so the JSON schema 
# work like a template for format definition, regex builder and content parser.
# Check if we can maintain the pydantic mapping or we need to create a func to convert JSON to FormatDefinition instance,
# which also validate the format definition and raise error if invalid.
class FormatDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    name:             str
    version:          str
    syntaxtype:       str
    variables:        VariableDefinition 
    links:            LinkDefinition
    macros:           MacroDefinition = None
    operators:        dict[str, list[str]] = {}
    literals:         dict[str, list[str]] = {}
    formatting:       dict[str, list[str]] = {}
    # todo: update meta field to accept only list with 2 elements, else raise error, 
    # and update regex builder to build pattern for meta based on the opening and closing tokens 
    # defined in the list, and a group for the content in between.
    meta:             dict[str, list[str]] = {}
    special_passages: list[str]            = []


# todo: add getter methods for format definition fields, so we can handle missing fields gracefully in regex builder and content parser, 
# instead of checking for None every time. For example, get_variables() can return an empty VariableDefinition if variables is None, 
# so we can avoid checking for None in content parser when we want to check variable prefixes.
    @model_validator(mode="after")
    def validate_extra_fields(self) -> "FormatDefinition":
        extras = self.model_extra or {}
        for key, value in extras.items():
            if not isinstance(value, dict):
                raise ValueError(f"Field custom '{key}' deve essere dict[str, list[str]]")
            for token, patterns in value.items():
                if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
                    raise ValueError(
                        f"Field custom '{key}.{token}' deve essere list[str]"
                    )
        return self

# Delete this? Check after renderer implementation
    def is_variable(self, token: str) -> bool:
        if not self.variables:
            return False
        return (token.startswith(self.variables.global_prefix) or
                token.startswith(self.variables.local_prefix))

# Delete this? Check after renderer implementation
    def is_translatable_macro(self, macro_type: str) -> bool:
        if not self.macros or not self.macros.inner:
            return False
        """Return True if the macro produces text output, False otherwise."""
        # macros.inner maps categories to lists; we must search inside lists
        for lst in self.macros.inner.values():
            if macro_type in lst:
                return True
        return False
    
    def is_special_passage(self, token: str) -> bool:
        if not self.special_passages:
            return False
        return token in self.special_passages   
    
    
from pydantic import BaseModel


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


class FormatDefinition(BaseModel):
    name:             str
    version:          str
    variables:        VariableDefinition 
    macros:           MacroDefinition = None
    links:            LinkDefinition
    operators:        dict[str, list[str]] = {}
    literals:         dict[str, list[str]] = {}
    formatting:       dict[str, list[str]] = {}
    media:            dict[str, str]       = {}
    special_passages: list[str]            = []


# Delete this? Check after renderer implementation
    def is_variable(self, token: str) -> bool:
        if not self.variables:
            return False
        return (token.startswith(self.variables.global_prefix) or
                token.startswith(self.variables.local_prefix))

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
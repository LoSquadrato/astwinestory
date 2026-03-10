from pydantic import BaseModel


class VariableDefinition(BaseModel):
    global_prefix: str        # '$'
    local_prefix:  str        # '_'


class MacroDefinition(BaseModel):
    open:       str                 # '<<' | '('
    close:      str                 # '>>' | ')'
    close_tag:  str 
    inner:      dict[str, list[str]] = {}
    
    
class LinkDefinition(BaseModel):
    open:             str       
    close:            str
    separator_target: str
    separator_setter: str


class FormatDefinition(BaseModel):
    name:             str
    version:          str
    variables:        VariableDefinition = None
    macros:           MacroDefinition = None
    links:            LinkDefinition = None
    operators:        dict[str, list[str]] = {}
    literals:         dict[str, list[str]] = {}
    formatting:       dict[str, list[str]] = {}
    media:            dict[str, str]       = {}
    special_passages: list[str]            = []


    def is_variable(self, token: str) -> bool:
        if not self.variables:
            return False
        return (token.startswith(self.variables.global_prefix) or
                token.startswith(self.variables.local_prefix))

    def is_translatable_macro(self, macro_type: str) -> bool:
        if not self.macros:
            return False
        """Restituisce True se la macro genera TextNode (output), False altrimenti."""
        return macro_type in self.macros.inner.values()
    
    
    def is_special_passage(self, token: str) -> bool:
        if not self.special_passages:
            return False
        return token in self.special_passages   
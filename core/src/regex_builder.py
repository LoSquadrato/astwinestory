import re
from core.formats import FormatDefinition


class RegexBuilder:
    def __init__(self, fmt: FormatDefinition):
        self._fmt = fmt
        self._patterns: dict[str, re.Pattern] = {}
        self._build()

    # Dict key -> pattern 
    # if None in fmt: builders.key = None
    def _build(self) -> None:
        builders = {
            "variable":        self._build_variable_pattern,
            "macro":           self._build_macro_pattern,
            "link":            self._build_link_pattern,
            "operator":        self._build_operator_pattern,
            "literal":         self._build_literal_pattern,
            "formatting":      self._build_formatting_pattern,
            "meta":            self._build_meta_pattern,
            "html":            self._build_html_pattern,
            "hook":            self._build_linear_hook_pattern
        }
        for key, builder in builders.items():
            pattern = builder()
            if pattern is not None:
                self._patterns[key] = pattern
        # build custom patterns from model_extra field, if any and add them to the patterns dict
        # self._patterns.update(self._build_custom_patterns())

    # getter method
    def get(self, key: str) -> re.Pattern | None:
        return self._patterns.get(key)

    # watcher method for available patterns, used in content parser to check if a pattern is available before trying to match it
    def available(self) -> list[str]:
        return list(self._patterns.keys())
    
    def get_key_list(self, mode: str) -> list[str] | None:
        if mode == "passage":
            return ["macro", "html", "link", "variable", "meta", "formatting"]
        elif mode == "node":
            return ["variable", "macro", "html", "meta",  "operator", "literal", "formatting"]
        else:
            return None
            
######################################################################
    # Private builder func create pattern for every format field
######################################################################
    # TODO: update pattern builder to include key group in the pattern, 
    # so we can identify which pattern matched in the content parser
    def _build_custom_patterns(self) -> dict[str, re.Pattern]:
        result = {}
        for field_name, field_data in self._fmt.model_extra.items():
            tokens = [(re.compile(rf'|(?P<{field_name}>{re.escape(p)})')) for patterns in field_data.values() for p in patterns]
            if tokens:
                result[field_name] = re.compile("|".join(tokens))
        return result
       
    
    def _build_variable_pattern(self) -> re.Pattern | None:
        if not self._fmt.variables:
            return None
        prefixes = []
        if self._fmt.variables.global_prefix:
            prefixes.append(re.escape(self._fmt.variables.global_prefix))
        if self._fmt.variables.local_prefix:
            prefixes.append(re.escape(self._fmt.variables.local_prefix))
        if not prefixes:
            return None
        return re.compile(rf'(?P<var_prefix>{"|".join(prefixes)})(?P<var_name>\w+)')

# TODO: update macro pattern to handle stack style parsing for nested macros:
# MACRO_START = re.compile(rf'{re.escape(op)}(?P<macro_type>\w[\w-]*:?)')
# TODO: add an escaped character ignore method
    def _build_macro_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros:
            return None
        op = self._fmt.macros.open
        cl = self._fmt.macros.close
        if not op or not cl:
            return None
        return re.compile(
                rf'{re.escape(op)}(?P<macro_type>\w[\w-]*:?)\s*(?P<macro_inner>.*?){re.escape(cl)}',
                re.DOTALL
            )   
    
    def _build_link_pattern(self) -> re.Pattern | None:
        if not self._fmt.links:
            return None
        op = self._fmt.links.open
        cl = self._fmt.links.close
        if not op or not cl:
            return None
        
        separators = getattr(self._fmt.links, "separators", [])
        escaped_op = re.escape(op)
        escaped_cl = re.escape(cl)
        
        if separators:
            sep_pattern = '|'.join(re.escape(s) for s in separators)
            return re.compile(
                rf'({escaped_op})'
                rf'(?:(?P<link_display>.+?)(?:{sep_pattern})(?P<link_target>.+?)'
                rf'|(?P<link_inner>[^{re.escape(cl[0])}]+?))'
                rf'({escaped_cl})',
                re.DOTALL
            )
        else:
            return re.compile(
                rf'({escaped_op})(?P<link_inner>[^{re.escape(cl[0])}]+?)({escaped_cl})',
                re.DOTALL
            )
          
            
    def _build_operator_pattern(self) -> re.Pattern | None:
        if not self._fmt.operators:
            return None
        opts = sorted(
            (opt for opts in self._fmt.operators.values() for opt in opts),
            key=len, reverse=True
        )
        if not opts:
            return None
        return re.compile(r'|'.join(re.escape(opt) for opt in opts))


    def _build_literal_pattern(self) -> re.Pattern | None:
        if not self._fmt.literals:
            return None
        lits = sorted(
            (lit for lits in self._fmt.literals.values() for lit in lits),
            key=len, reverse=True
        )
        if not lits:
            return None
        return re.compile(r'|'.join(rf'{re.escape(lit)}(\w.*?){re.escape(lit)}' for lit in lits))



    def _build_formatting_pattern(self) -> re.Pattern | None:
        if not self._fmt.formatting:
            return None
        fmts = sorted(
            (f for fmts in self._fmt.formatting.values() for f in fmts),
            key=len, reverse=True
        )
        if not fmts:
            return None
        return re.compile(r'|'.join(re.escape(f) for f in fmts))


    def _build_meta_pattern(self) -> re.Pattern | None:
        if not self._fmt.meta:
            return None
        opens = []
        closes = []
        for tokens in self._fmt.meta.values():
            opens.append(re.escape(tokens[0]))
            closes.append(re.escape(tokens[1]))
        if not opens or not closes:
            return None
        return re.compile(
            rf'(?P<meta_prefix>{"|".join(opens)})'
            rf'(?P<meta_content>.*?)'
            rf'(?P<meta_suffix>{"|".join(closes)})', re.DOTALL)
        
        
    def _build_html_pattern(self) -> re.Pattern | None:
        if not self._fmt.html:
            return None
        op = self._fmt.html.open
        cl = self._fmt.html.close
        if not op or not cl:
            return None
        return re.compile(
            rf'{re.escape(op)}(?P<html_tag>\w[\w-]*:?)\s*{re.escape(cl)}',
            re.DOTALL
        )
        
    def _build_linear_hook_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros:
            return None
        op = self._fmt.macros.hook_open
        cl = self._fmt.macros.hook_close
        if not op or not cl:
            return None
        return re.compile(
                rf"(?P<opener>{re.escape(op)})|(?P<closer>{re.escape(cl)})",
                re.DOTALL
            )
        
######################################################################
    # Public builder func group pattern for parsing func
######################################################################
           
    def build_pattern(self, keys: list[str]) -> re.Pattern | None:
        parts = []
        for key in keys:
            pattern = self._patterns.get(key)
            if pattern is not None:
                parts.append(f'(?P<{key}>{pattern.pattern})')
        if not parts:
            return None
        return re.compile(r'|'.join(parts), re.DOTALL)
    
    def build_title_pattern(self) -> re.Pattern:
        return re.compile(
            r'^::\s*(?P<title>[^\[\]{}\n]+?)\s*'
            r'(?:\[(?P<tags>[^\]]*)\])?\s*'
            r'(?:\{(?P<metadata>[^\}]*)\})?\s*$',
            re.MULTILINE
        )
        
    def build_passage_content_pattern(self) -> re.Pattern | None:
        return self.build_pattern(self.get_key_list("passage"))
    
    def build_node_content_pattern(self) -> re.Pattern | None:
        return self.build_pattern(self.get_key_list("node"))
      
    def build_macro_content_pattern(self) -> re.Pattern | None:
        # after findind a macro start this pattern work with a stack based function 
        # to extract the whole macro content, including nested macros
        op = self._fmt.macros.open
        cl = self._fmt.macros.close
        if not op or not cl:
            return None
        if self._fmt.get_syntaxtype() == "markup":
            close_tag = re.escape(self._fmt.macros.close_tag) if self._fmt.macros.close_tag else ""
            macro_type = rf"(?:{close_tag})?\w[\w-]*:?"
            return re.compile(
                rf"{re.escape(op)}(?P<macro_type>{macro_type})(?:\s+(?P<macro_inner>.*?))?{re.escape(cl)}",
                re.DOTALL
            )
        if self._fmt.get_syntaxtype() == "linear":
            macro_type = rf"\w[\w-]*:?"
            return re.compile(
                rf"(?P<opener>{re.escape(op)}{macro_type})|(?P<closer>{re.escape(cl)})",
                re.DOTALL
            )
        return None
    
    def build_html_content_pattern(self) -> re.Pattern | None:
        # after findind a html start this pattern work with a stack based function 
        # to extract the whole html content, including nested html
        op = self._fmt.html.open
        cl = self._fmt.html.close
        if not op or not cl:
            return None
        close_tag = re.escape(self._fmt.html.close_tag) if self._fmt.html.close_tag else ""
        html_type = rf"(?:{close_tag})?\w[\w-]*:?"
        return re.compile(
            rf"{re.escape(op)}(?P<html_tag>{html_type})(?:\s+(?P<html_inner>.*?))?{re.escape(cl)}",
            re.DOTALL
        )
    
    def build_hook_content_pattern(self) -> re.Pattern | None:
        return self.build_pattern(["hook"])
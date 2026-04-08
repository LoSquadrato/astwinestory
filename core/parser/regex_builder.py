import re
from core.formats.format_definition import FormatDefinition


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
            "macro":           self._build_macro_start_pattern,
            "inner":           self._build_inner_pattern, # deprecated
            "link":            self._build_link_pattern,
            "operator":        self._build_operator_pattern,
            "literal":         self._build_literal_pattern,
            "formatting":      self._build_formatting_pattern,
            "meta":            self._build_meta_pattern,
            "special_passage": self._build_special_passage_pattern,
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
            return ["macro", "link", "variable", "meta", "formatting"]
        elif mode == "node":
            return ["variable", "macro", "meta", "operator", "literal", "formatting"]
        else:
            return None
            
######################################################################
    # Private builder func create pattern for every format field
######################################################################
    # todo: update pattern builder to include key group in the pattern, 
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
        return re.compile(rf'(?:{"|".join(prefixes)})\w+')

# todo: update macro pattern to handle stack style parsing for nested macros:
# MACRO_START = re.compile(rf'{re.escape(op)}(?P<macro_type>\w[\w-]*:?)')
   
    def _build_macro_start_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros:
            return None
        op = self._fmt.macros.open
        cl = self._fmt.macros.close
        if not op or not cl:
            return None
        return re.compile(rf'({re.escape(op)})(?P<macro_type>\w[\w-]*:?)')
        
    # todo: update after resolve operator pattern builder errors
    def _build_inner_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros or not self._fmt.macros.inner:
            return None
        lits = sorted(
            (lit for lits in self._fmt.literals.values() for lit in lits),
            key=len, reverse=True
        )
        if not lits:
            return None
        return re.compile(r'|'.join(re.escape(lit) for lit in lits))
    
        
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
                rf'{escaped_op}'
                rf'(?:(?P<link_display>.+?)(?:{sep_pattern})(?P<link_target>.+?)'
                rf'|(?P<link_inner>[^{re.escape(cl[0])}]+?))'
                rf'{escaped_cl}',
                re.DOTALL
            )
        else:
            return re.compile(
                rf'{escaped_op}(?P<link_inner>[^{re.escape(cl[0])}]+?){escaped_cl}',
                re.DOTALL
            )

# todo: DRY up the pattern builders for operator/literal/formatting/meta/special_passage, they all follow the same structure
    def _build_operator_pattern(self) -> re.Pattern | None:
        if not self._fmt.operators:
            return None
        lits = sorted(
            (lit for lits in self._fmt.operators.values() for lit in lits),
            key=len, reverse=True
        )
        if not lits:
            return None
        return re.compile(r'|'.join(re.escape(lit) for lit in lits))

    def _build_literal_pattern(self) -> re.Pattern | None:
        if not self._fmt.literals:
            return None
        lits = sorted(
            (lit for lits in self._fmt.literals.values() for lit in lits),
            key=len, reverse=True
        )
        if not lits:
            return None
        return re.compile(r'|'.join(re.escape(lit) for lit in lits))

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
        metas = []
        for key, tokens in self._fmt.meta.items():
            metas.append(
                # key group maybe don't work, make a try
                rf'(?P<{key}>'
                rf'({re.escape(tokens[0])})'
                rf'.+?'
                rf'({re.escape(tokens[1])})'
                rf')'
            )
        if not metas:
            return None
        return re.compile(r'|'.join(metas), re.DOTALL)

    def _build_special_passage_pattern(self) -> re.Pattern | None:
        if not self._fmt.special_passages:
            return None
        sps = sorted(self._fmt.special_passages, key=len, reverse=True)
        return re.compile(r'|'.join(re.escape(sp) for sp in sps))
    
    
######################################################################
    # Public builder func group pattern for parsing func
######################################################################
           
    def build_combined_pattern(self, keys: list[str]) -> re.Pattern | None:
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
    
    # deprecated, replaced by build_passage_content_pattern 
    # which only includes patterns valid in passage content
    def build_content_pattern(self) -> re.Pattern | None:
        parts = []
        for key in ("macro", "link", "variable", "operator"):
            pattern = self._patterns.get(key)
            if pattern is not None:
                parts.append(f"(?P<{key}>{pattern.pattern})")
        if not parts:
            return None
        return re.compile("|".join(parts), re.DOTALL)
    
    def build_node_content_pattern(self) -> re.Pattern | None:
        return self.build_combined_pattern(self.get_key_list("node"))
    
    def build_macro_iteration_pattern(self) -> re.Pattern | None:
        # after findind a macro start this pattern work with a stack based function 
        # to extract the whole macro content, including nested macros
        op = self._fmt.macros.open
        cl = self._fmt.macros.close
        if not op or not cl:
            return None
        return re.compile(rf'({re.escape(op)})|({re.escape(cl)})', re.DOTALL)
    
    def build_passage_content_pattern(self) -> re.Pattern | None:
        return self.build_combined_pattern(self.get_key_list("passage"))
    
    def build_macro_with_stack_pattern(self) -> re.Pattern | None:
        # this pattern is used to parse the full content of a macro after it has been extracted with the stack function
        # it should match the same constructs as the macro inner pattern, but also include links and special passages, which are valid inside macros
        op = self._fmt.macros.open
        cl = self._fmt.macros.close
        if not op or not cl:
            return None
        return re.compile(
            rf'{re.escape(op)}(?P<macro_type>\w[\w-]*:?)\s*(?P<macro_inner>.*){re.escape(cl)}',
            re.DOTALL
        )
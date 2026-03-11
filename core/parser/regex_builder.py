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
            "macro":           self._build_macro_pattern,
            "inner":           self._build_inner_pattern,
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

    # getter method
    def get(self, key: str) -> re.Pattern | None:
        return self._patterns.get(key)

    def available(self) -> list[str]:
        return list(self._patterns.keys())

    
######################################################################
    # Private builder func create pattern for every format field
######################################################################
    
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

    def _build_macro_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros:
            return None
        op = self._fmt.macros.open
        cl = self._fmt.macros.close
        if not op or not cl:
            return None
        return re.compile(
            rf'{re.escape(op)}(?P<macro_type>\w[\w\-]*:?)(?P<macro_inner>.*?){re.escape(cl)}',
            re.DOTALL
        )
        
    def _build_inner_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros:
            return None
        inner = sorted(
            (ins for inner in self._fmt.macros.inner.values() for ins in inner),
            key=len, reverse=True   
        )
        if not inner:
            return None
        return re.compile(r'|'.join(re.escape(ins) for ins in inner))
        
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

    def _build_operator_pattern(self) -> re.Pattern | None:
        if not self._fmt.operators:
            return None
        ops = sorted(
            (op for ops in self._fmt.operators.values() for op in ops if not op.isalpha()),
            key=len, reverse=True
        )
        if not ops:
            return None
        return re.compile(r'|'.join(re.escape(op) for op in ops))

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
        metas = sorted(
            (m for metas in self._fmt.meta.values() for m in metas),
            key=len, reverse=True
        )
        if not metas:
            return None
        return re.compile(r'|'.join(re.escape(m) for m in metas))

    def _build_special_passage_pattern(self) -> re.Pattern | None:
        if not self._fmt.special_passages:
            return None
        sps = sorted(self._fmt.special_passages, key=len, reverse=True)
        return re.compile(r'|'.join(re.escape(sp) for sp in sps))
    
    
######################################################################
    # Public builder func group pattern for parsing func
######################################################################
           
    def build_combined_pattern(self) -> re.Pattern | None:
        parts = []
        for key, pattern in self._patterns.items():
            parts.append(f'(?P<{key}>{pattern.pattern})')
        if not parts:
            return None
        return re.compile(r'|'.join(parts), re.DOTALL)
    
    def build_title_pattern(self) -> re.Pattern:
        return re.compile(r'^\s*::\s*(?P<passage_name>[^\[\{]+?)(?:\s*\[|\s*\{|$)', re.MULTILINE)
    
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
    
    def build_macro_inner_pattern(self) -> re.Pattern | None:
        # This pattern is used to parse the inner content of macros, 
        # which may contain nested macros. It should match the same constructs as the content pattern,
        # excluding link and special_passage patterns, which are not valid inside macros.
        # the key pattern order has to be: 
        # variable, macro, media, operator, literal, formatting
        parts = []
        for key in ("variable", "macro", "media", "operator", "literal", "formatting"):
            pattern = self._patterns.get(key)
            if pattern is not None:
                parts.append(f"(?P<{key}>{pattern.pattern})")
        if not parts:
            return None
        return re.compile("|".join(parts), re.DOTALL)
    
    def build_passage_content_pattern(self) -> re.Pattern | None:
        # same as content pattern, but only macros/links/variables/media 
        # that are valid in passage content (e.g. no operators)
        parts = []
        for key in ("macro", "link", "variable", "media"):
            pattern = self._patterns.get(key)
            if pattern is not None:
                parts.append(f"(?P<{key}>{pattern.pattern})")
        if not parts:
            return None
        return re.compile("|".join(parts), re.DOTALL)
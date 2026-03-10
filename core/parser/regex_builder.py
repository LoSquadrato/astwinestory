'''
import re
from core.formats.format_definition import FormatDefinition


class RegexBuilder:
    def __init__(self, fmt: FormatDefinition):
        self.variable_pattern          = self.build_variable_pattern(fmt)
        self.macro_pattern             = self.build_macro_pattern(fmt)
        self.link_pattern              = self.build_link_pattern(fmt)
        self.operator_pattern          = self.build_operator_pattern(fmt)
        self.literal_pattern           = self.build_literal_pattern(fmt)
        self.formatting_pattern        = self.build_formatting_pattern(fmt)
        self.media_pattern             = self.build_media_pattern(fmt)
        self.special_passage_pattern   = self.build_special_passage_pattern(fmt)

    @staticmethod
    def build_variable_pattern(fmt: FormatDefinition) -> re.Pattern:
        # matcha sia variabili globali ($) che locali (_)
        global_prefix = re.escape(fmt.variables.global_prefix)
        local_prefix  = re.escape(fmt.variables.local_prefix)
        return re.compile(rf'(?:{global_prefix}|{local_prefix})\w+')

    @staticmethod
    def build_macro_pattern(fmt: FormatDefinition) -> re.Pattern:
        op = re.escape(fmt.macros.open)
        cl = re.escape(fmt.macros.close)
        return re.compile(rf'{op}(.+?){cl}', re.DOTALL)

    @staticmethod
    def build_link_pattern(fmt: FormatDefinition) -> re.Pattern:
        op = re.escape(fmt.links.open)
        cl = re.escape(fmt.links.close)
        return re.compile(rf'{op}(.+?){cl}')

    @staticmethod
    def build_operator_pattern(fmt: FormatDefinition) -> re.Pattern:
        # ordinati per lunghezza decrescente per evitare match parziali (es. ">=" prima di ">")
        ops = sorted(
            (op for ops in fmt.operators.values() for op in ops),
            key=len, reverse=True
        )
        escaped = [re.escape(op) for op in ops]
        return re.compile(r'|'.join(escaped))

    @staticmethod
    def build_literal_pattern(fmt: FormatDefinition) -> re.Pattern:
        lits = sorted(
            (lit for lits in fmt.literals.values() for lit in lits),
            key=len, reverse=True
        )
        escaped = [re.escape(lit) for lit in lits]
        return re.compile(r'|'.join(escaped))

    @staticmethod
    def build_formatting_pattern(fmt: FormatDefinition) -> re.Pattern:
        fmts = sorted(
            (f for fmts in fmt.formatting.values() for f in fmts),
            key=len, reverse=True
        )
        escaped = [re.escape(f) for f in fmts]
        return re.compile(r'|'.join(escaped))

    @staticmethod
    def build_media_pattern(fmt: FormatDefinition) -> re.Pattern:
        meds = sorted(
            (m for meds in fmt.media.values() for m in meds),
            key=len, reverse=True
        )
        escaped = [re.escape(m) for m in meds]
        return re.compile(r'|'.join(escaped))

    @staticmethod
    def build_special_passage_pattern(fmt: FormatDefinition) -> re.Pattern:
        sps = sorted(fmt.special_passages, key=len, reverse=True)
        escaped = [re.escape(sp) for sp in sps]
        return re.compile(r'|'.join(escaped))
'''   
##########################################################

import re
from core.formats.format_definition import FormatDefinition


class RegexBuilder:
    def __init__(self, fmt: FormatDefinition):
        self._fmt = fmt
        self._patterns: dict[str, re.Pattern] = {}
        self._build()

    def _build(self) -> None:
        """Costruisce i pattern iterando sul contenuto del FormatDefinition.
        Un gruppo viene compilato solo se ha contenuto nel JSON."""

        builders = {
            "variable":        self._build_variable_pattern,
            "macro":           self._build_macro_pattern,
            "inner":           self._build_inner_pattern,
            "link":            self._build_link_pattern,
            "operator":        self._build_operator_pattern,
            "literal":         self._build_literal_pattern,
            "formatting":      self._build_formatting_pattern,
            "media":           self._build_media_pattern,
            "special_passage": self._build_special_passage_pattern,
        }

        for key, builder in builders.items():
            pattern = builder()
            if pattern is not None:
                self._patterns[key] = pattern

    def get(self, key: str) -> re.Pattern | None:
        """Restituisce il pattern per la chiave richiesta, None se non disponibile."""
        return self._patterns.get(key)

    def available(self) -> list[str]:
        """Restituisce le chiavi dei pattern disponibili per questo formato."""
        return list(self._patterns.keys())

    # ── builder privati ──────────────────────────────────────────────────────

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
        return re.compile(rf'(?P<variable>:{"|".join(prefixes)})\w+')

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
        return re.compile(rf'{re.escape(op)}(?P<link_inner>[^{re.escape(cl[0])}]+?){re.escape(cl)}')

    def _build_operator_pattern(self) -> re.Pattern | None:
        if not self._fmt.operators:
            return None
        ops = sorted(
            (op for ops in self._fmt.operators.values() for op in ops),
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

    def _build_media_pattern(self) -> re.Pattern | None:
        if not self._fmt.media:
            return None
        meds = sorted(
            (m for meds in self._fmt.media.values() for m in meds),
            key=len, reverse=True
        )
        if not meds:
            return None
        return re.compile(r'|'.join(re.escape(m) for m in meds))

    def _build_special_passage_pattern(self) -> re.Pattern | None:
        if not self._fmt.special_passages:
            return None
        sps = sorted(self._fmt.special_passages, key=len, reverse=True)
        return re.compile(r'|'.join(re.escape(sp) for sp in sps))
    
    def build_combined_pattern(self) -> re.Pattern | None:
        parts = []
        for key, pattern in self._patterns.items():
            parts.append(f'(?P<{key}>{pattern.pattern})')
        if not parts:
            return None
        return re.compile(r'|'.join(parts), re.DOTALL)
    
    def build_title_pattern(self) -> re.Pattern:
        return re.compile(r'^::\s*(?P<passage_name>[^\[\{]+?)(?:\s*\[|\s*\{|$)', re.MULTILINE)
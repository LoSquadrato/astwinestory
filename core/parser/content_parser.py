import re
import textwrap
from dataclasses import dataclass
from itertools import count
from .regex_builder import RegexBuilder
from core.formats.format_definition import FormatDefinition
from core.ast import (
    Node,
    Passage,
    Story,
    TextNode,
    VariableNode,
    MacroNode,
    LinkNode,
    OperatorNode,
    MetaNode
)

class ParsingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ParsingError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        

@dataclass
class Parser:
    
    def __init__(self, format_def: FormatDefinition):
        # defensive: ensure essential sections exist
        if not format_def:
            raise ParsingError(["Missing format definition"])
        if not hasattr(format_def, 'macros'):
            raise ParsingError(["Format definition missing macros configuration"])
        if not hasattr(format_def, 'links'):
            raise ParsingError(["Format definition missing links configuration"])
        self.format_def = format_def
        self._counter = count(1)
        self._patterns = RegexBuilder(format_def)

    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, kind: str, match) -> Node:
        match kind:
            case "link":
                link_inner = match.group("link_inner")
                display, target = self._parse_link_parts(link_inner)
                return LinkNode(
                    node_id=self._next_id(),
                    display=display,
                    target=target
                )
            case "variable":
                var_name = match.group("variable")
                scope = "global" if var_name.startswith(self.format_def.variables.global_prefix) else "local"
                return VariableNode(
                    node_id=self._next_id(),
                    name=var_name,
                    scope=scope
                )
            case "macro":
                macro_type = match.group("macro_type")
                return MacroNode(
                    node_id=self._next_id(),
                    macro_type=macro_type,
                    children=[]
                )
            case "operator":
                return OperatorNode(
                    node_id=self._next_id(),
                    operator=match.group("operator")
                )
            case "meta":
                return MetaNode(
                    node_id=self._next_id(),
                    kind="meta",
                    raw=match.group("meta_raw")
                )
            case _:
                raise ParsingError([f"Unknown node type: {kind}"])

    def _build_content_pattern(self) -> re.Pattern | None:
        parts = []
        for key in ("macro", "link", "variable", "operator"):
            pattern = self._patterns.get(key)
            if pattern is not None:
                parts.append(f"(?P<{key}>{pattern.pattern})")
        if not parts:
            return None
        return re.compile("|".join(parts), re.DOTALL)

    def _parse_link_parts(self, link_inner: str) -> tuple[str, str]:
        if "->" in link_inner:
            display, target = link_inner.split("->", 1)
            return display.strip(), target.strip()
        if "<-" in link_inner:
            target, display = link_inner.split("<-", 1)
            return display.strip(), target.strip()
        if "|" in link_inner:
            display, target = link_inner.split("|", 1)
            return display.strip(), target.strip()
        token = link_inner.strip()
        return token, token
        
    
    def parse_story(self, passage_list: list[str]) -> Story:
        return Story(
            title=self.get_passage_name(passage_list[0]) or "Untitled Story",
            format=self.format_def.name,
            passages=[self.parse_passage(passage) for passage in passage_list]
        )

    def parse_passage(self, raw: str) -> Passage:            
        body = self._extract_passage_body(raw)
        return Passage(
            node_id=self._next_id(),
            name=self.get_passage_name(raw),
            children=self.parse_content(body)
        )

    def _extract_passage_body(self, raw: str) -> str:
        stripped = raw.lstrip()
        _, _, remainder = stripped.partition("\n")
        return remainder

    def parse_content(self, text: str) -> list[Node]:
        if not self.format_def.macros and not self.format_def.links:
            raise ParsingError(["No macro/link patterns available for this format definition"])
        nodes = []
        pivot = 0
        pattern = self._build_content_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        for match in pattern.finditer(text):
            if match.start() > pivot:
                raw_text = text[pivot:match.start()]
                nodes.append(TextNode(node_id=self._next_id(), value=raw_text))
            kind = match.lastgroup
            if kind is None:
                raise ParsingError([f"Regex match missing group: {match}"])
            node = self._build_node(kind, match)
            if kind == "macro":
                inner = match.group("macro_inner")
                node.children = self.parse_content(inner)
            if kind == "link":
                inner = node.display
                node.children = self.parse_content(inner) if inner else []
            nodes.append(node)
            pivot = match.end()

        if pivot < len(text):
            nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:]))
        return nodes
    
    def get_passage_name(self, text: str) -> str | None:
        pattern = self._patterns.build_title_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        match = pattern.search(text)
        if match:
            return match.group("passage_name").strip() 
        return None
    
    @staticmethod
    def split_passage(text: str) -> list[str]:
        text = textwrap.dedent(text)
        if "::" in text and "\n" not in text:
            raise ParsingError([
                "The file contains '::' but no newline characters. "
                "The Twee file may have been flattened into a single line."
            ])
        passage_cut = re.compile(r"(?=^\s*::)", re.MULTILINE)
        passages_list = passage_cut.split(text)
        return [passage for passage in passages_list if passage.strip()]
    
    
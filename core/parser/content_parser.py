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
    MetaNode,
    LiteralNode,
    FormattingNode
)

class ParsingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ParsingError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        

@dataclass
class Parser:
    
    def __init__(self, format_def: FormatDefinition):
        self.format_def = format_def
        self._counter = count(1)
        self._patterns = RegexBuilder(format_def)

    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, kind: str, match) -> Node:
        match kind:
            case "link":
                display = match.group("link_display")
                target  = match.group("link_target") or match.group("link_inner")
                return LinkNode(
                    node_id=self._next_id(),
                    display=display,
                    children=self.parse_content(target, self._patterns.build_macro_inner_pattern())
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
                children = match.group("macro_inner")
                return MacroNode(
                    node_id=self._next_id(),
                    macro_type=macro_type,
                    children=self.parse_content(children, self._patterns.build_macro_inner_pattern())
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
            case "literal":
                return LiteralNode(
                    node_id=self._next_id(),
                    value=match.group("literal")
                )
            case "formatting":
                return FormattingNode(
                    node_id=self._next_id(),
                    value=match.group("formatting")
                )
            case _:
                raise ParsingError([f"Unknown node type: {kind}"])

    
    def parse_story(self, passage_list: list[str]) -> Story:
        title = self.get_passage_name(passage_list[0]) or "Untitled Story"
        passages= []
        for passage in passage_list:
            try:
                passages.append(self.parse_passage(passage))
            except ParsingError as e:
                raise ParsingError([f"Error parsing passage '{title}':"] + e.errors)
        return Story(
            title=title,
            format=self.format_def.name,
            format_version=self.format_def.version,
            passages=passages
        )

# todo: title line contains tags and metadata, 
# need to parse those separately and store in Passage object
    def parse_passage(self, raw: str) -> Passage:
        name = self.get_passage_name(raw)
        if not name:
            raise ParsingError([f"Passage missing title: {raw[:30]}..."])
        if self.format_def.is_special_passage(name):
            return Passage(
                node_id=self._next_id(),
                name=name,
                children=[TextNode(node_id=self._next_id(), value=raw)]
            )
        children = self.parse_content(
            raw, 
            self._patterns.build_passage_content_pattern()
        )
        if not children:
            raise ParsingError([f"Passage '{name}' has no content."])     
        return Passage(
            node_id=self._next_id(),
            name=name,
            children=children
        )

# todo: macro nodes need to be parsed with a stack to handle nesting
    def parse_content(self, text: str, pattern: re.Pattern) -> list[Node]:
        # find matches for macros, links, variables, media pass them to _build_node, 
        # and recursively parse_macro_nodes for macros
        nodes = [] 
        pivot = 0
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
    
    
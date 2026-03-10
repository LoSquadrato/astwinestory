import re
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
        self.format_def = format_def
        self._counter = count(1)
        self._patterns = RegexBuilder(format_def)

    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, kind: str, match) -> Node:
        match kind:
            case "link":
                return LinkNode(
                    node_id=self._next_id(),
                    display=match.group("link_display"),
                    target=match.group("link_target")
                )
            case "variable":
                var_name = match.group("var_name")
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
                    raw=match.group("meta_raw")
                )
            case _:
                raise ParsingError([f"Unknown node type: {kind}"])
        
    
    def parse_story(self, passage_list: list[str]) -> Story:
        return Story(
            title=self.get_passage_name(passage_list[0]) or "Untitled Story",
            format=self.format_def.name,
            passages=[self.parse_passage(passage) for passage in passage_list]
        )

    def parse_passage(self, raw: str) -> Passage:            
        return Passage(
            node_id=self._next_id(),
            name=self.get_passage_name(raw),
            children=self.parse_content(raw)
        )

    def parse_content(self, text: str) -> list[Node]:
        nodes = []
        pivot = 0
        matches = self._patterns.build_combined_pattern().finditer(text)
        if matches:
            for match in matches:
                # testo prima del match → TextNode
                if match.start() > pivot:
                    raw_text = text[pivot:match.start()]
                    nodes.append(TextNode(node_id=self._next_id(), value=raw_text))
                # identifica il tipo dal gruppo che ha fatto match
                kind = match.lastgroup
                if kind is None:
                    raise ParsingError([f"Regex match senza gruppo identificativo: {match}"])
                nodes.append(self._build_node(kind, match))
                if kind == "macro":
                    text = match.group("macro_inner")
                    nodes.extend(self.parse_content(text))
                if kind == "link":
                    text = match.group("link_inner")
                    nodes.extend(self.parse_content(text))                      
                # logica per estrazione nodi interni
                pivot = match.end()
            # testo dopo l'ultimo match → TextNode
            if pivot < len(text):
                nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:]))
        return nodes
    
    def get_passage_name(self, text: str) -> str | None:
        match = self._patterns.build_title_pattern().search(text)
        if match:
            return match.group("passage_name").strip() 
        return None
    
    @staticmethod
    def split_passage(text: str) -> list[str]:
        if "::" in text and "\n" not in text:
            raise ParsingError([
                "The file contains '::' but no newline characters. "
                "The Twee file may have been flattened into a single line."
            ])
        passage_cut = re.compile(r"(?=^::)", re.MULTILINE)
        passages_list = passage_cut.split(text)
        return passages_list[1:]
    
    
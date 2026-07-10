# TODO: dividiamo le macro in due gruppi: quelle che hanno un exit tag e quelle che non ce l'hanno. 
# per la definizione delle prime è necessario sia presente anche il tag di chiusura, per le seconde no.
# ES SugarCube: <<if>> <<print>> <<else>> <<print>> <</if>>  diventa in Harlowe: (if:)[(print:)] (else-if:)[(print:)]

import textwrap
import re
from itertools import count

from .extractor import Extractor
from .regex_builder import RegexBuilder
from core.formats.format_definition import FormatDefinition
from core.ast import (
    Node,
    Passage,
    Story,
    TextNode,
    VariableNode,
    LinkNode,
    OperatorNode,
    MetaNode,
    LiteralNode,
    FormattingNode,
    MacroNode,
    HTMLNode
)

class ParsingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ParsingError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        
        
class Parser:
    def __init__(self, format_def: FormatDefinition):
        self.format_def = format_def
        self._counter = count(1)
        self._patterns = RegexBuilder(format_def)
        self._extractor = Extractor(format_def, self._patterns)
        # self._build = Builder() -- da valutare, potrebbe tornare utile
        
    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, **kwargs) -> Node:
        kind = kwargs.get("kind")
        match = kwargs.get("match")
        match kind:
            case "link":
                display = match.group("link_display") if match.group("link_display") is not None else ""
                target  = match.group("link_target") or match.group("link_inner")
                return LinkNode(
                    node_id=self._next_id(),
                    display=display,
                    children=self.parse_content(target, 
                        self._patterns.build_node_content_pattern())
                    )
            case "variable":
                prefix = match.group("var_prefix")
                name = match.group("var_name")
                scope = "global_prefix" if prefix == self.format_def.variables.global_prefix else "local_prefix"
                return VariableNode(
                    node_id=self._next_id(),
                    name=name,
                    scope=scope
                )
            case "macro":
                macro_type = kwargs.get("macro_type")
                children = kwargs.get("children")
                hook = kwargs.get("hook") if "hook" in kwargs else None
                return MacroNode(
                    node_id=self._next_id(),
                    macro_type=macro_type,
                    children=self.parse_content(children, self._patterns.build_node_content_pattern()) if children else [],
                    hook=self.parse_content(hook, self._patterns.build_node_content_pattern()) if hook else None
                )
            case "html":
                tag = kwargs.get("tag")
                body = kwargs.get("body")
                return HTMLNode(
                    node_id=self._next_id(),
                    tag=tag,
                    body=body
                )
            case "operator":
                return OperatorNode(
                    node_id=self._next_id(),
                    operator=match.group(0)
                )
            case "meta":
                return MetaNode(
                    node_id=self._next_id(),
                    kind=match.group("meta_prefix"),
                    raw=match.group("meta_content")
                )
            case "literal":
                return LiteralNode(
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case "formatting":
                return FormattingNode(
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case _:
                raise ParsingError([f"Unknown node type: {kind}"])
        
    def parse_story(self, passage_list: list[str]) -> tuple[Story, int]:
        first_line = self.match_passage_first_line(passage_list[0])
        title = first_line.group("title") if first_line else "Untitled Story"
        passages= []
        for passage in passage_list:
            try:
                passages.append(self.parse_passage(passage))
            except ParsingError as e:
                raise ParsingError([f"Error parsing passage '{title}':"] + e.errors)
        return Story(
            title=title,
            format=self.format_def,
            format_version=self.format_def.version,
            passages=passages
        ), self._next_id()


    def parse_passage(self, raw: str) -> Passage:
        first_line = self.match_passage_first_line(raw)
        if first_line is None:
            raise ParsingError([f"Passage missing first line: {raw[:30]}..."])
        name = first_line.group("title")
        tags = first_line.group("tags") or ""
        metadata = first_line.group("metadata") or ""
        body = raw[first_line.end():].lstrip('\n')
        if not name:
            raise ParsingError([f"Passage missing title: {raw[:30]}..."])
        # special passages are parsed as plain text, without looking for macros/links/variables,
        # and stored as a single TextNode child of the Passage. This allows formats to define
        if self.format_def.is_special_passage(name):
            return Passage(
                node_id=self._next_id(),
                name=name,
                tags=tags,
                metadata=metadata,
                children=[TextNode(node_id=self._next_id(), value=body)]
            )
            
        children = self.parse_content(
            body, 
            self._patterns.build_passage_content_pattern()
        )
        if not children:
            children = [TextNode(node_id=self._next_id(), value="")] 
        return Passage(
            node_id=self._next_id(),
            name=name,
            tags=tags,
            metadata=metadata,
            children=children
        )
        
    # TODO: Add a logic like macro extractor to parse the content of a html macro in SugarCube.
    # 
    def parse_content(self, text: str, pattern: re.Pattern) -> list[Node]:
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        # find matches for macros, links, variables, media pass them to _build_node, 
        # and recursively parse_macro_nodes for macros
        nodes = [] 
        pivot = 0
        for match in pattern.finditer(text):
            if match.start() < pivot:
                continue  
            if match.start() > pivot:
                raw_text = text[pivot:match.start()]
                # TODO: DRY this and use build_node also for text node
                nodes.append(TextNode(node_id=self._next_id(), value=raw_text))
                pivot = match.start()
            kind = self._get_match_type(match)
            if kind is None:
                raise ParsingError([f"Regex match missing group: {match}"])
            args_builder = self.get_node_params(kind, match, text[pivot:])
            pivot += args_builder.get("offset", len(match.group(0)))
            node = self._build_node(**args_builder)
            nodes.append(node)
        if pivot < len(text):
            nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:]))
        # define macro groups for parsing macro's hook or macro content       
        return nodes
    
    # when refactoring defer to the Builder class this function may contain all kind of node
    def get_node_params(self, kind: str, match: re.Match, text: str) -> dict:
        if self.format_def.get_syntaxtype() == "markup" and kind == "macro":
            return self._extractor.get_macro_params_markup(text)
        if self.format_def.get_syntaxtype() == "linear" and kind == "macro":
            return self._extractor.get_macro_params_linear(text)
        if kind == "html":
            return self._extractor.get_html_params(text)
        return {"kind": kind, "match": match}
    
    
    def _get_match_type(self, match: re.Match) -> str | None:
        if match is None:
            return None
        for key in self._patterns.available():
            if key in match.groupdict() and match.group(key) is not None:
                return key
        return None 

    def match_passage_first_line(self, text: str) -> re.Match | None:
        pattern = self._patterns.build_title_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        match = pattern.search(text)
        if match:
            return match 
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
    
    
def story_parsing(text: str, format_def: FormatDefinition) -> tuple[Story, int]:
    parser = Parser(format_def)
    passages = Parser.split_passage(text)
    return parser.parse_story(passages)
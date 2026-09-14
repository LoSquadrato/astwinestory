# Simplified parser for story formats
# - add story field which contains the overall story structure
# - export the split passage function, parser has to only parse the passage content
# - 

import re
import textwrap
from itertools import count
from dataclasses import dataclass

from core.formats import FormatDefinition
from src.extractor import Extractor
from src.regex_builder import RegexBuilder 
from src.node import (
    Node,
    TextNode,
    VariableNode,
    HookNode,
    MacroNode,
    LinkNode,
    OperatorNode,
    MetaNode,
    HTMLNode,
    LiteralNode,
    FormattingNode,
    Passage
)


@dataclass
class Story:
    title:          str = ""
    format:         FormatDefinition | None = None
    format_version: str = ""
    passages:       list[Passage] = []
    
    
PASSAGE_FIRST_LINE_PATTERN = re.compile(
            r'^::\s*(?P<title>[^\[\]{}\n]+?)\s*'
            r'(?:\[(?P<tags>[^\]]*)\])?\s*'
            r'(?:\{(?P<metadata>[^\}]*)\})?\s*$',
            re.MULTILINE
        )

class ParsingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ParsingError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        
        
class Parser:
    def __init__(self, format_def: FormatDefinition, document: str):
        self.format_def = format_def
        self._counter = count(1)
        self._patterns = RegexBuilder(format_def)
        self._extractor = Extractor(format_def, self._patterns)
        self.story = Story()
        self.document = document # Raw document content to be parsed it can be used in case of big data buffering?
        # self._build = Builder() -- da valutare, potrebbe tornare utile
        
    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, params: dict) -> Node:
        kind = params["kind"]
        match kind:
            case "link":
                match = params["match"]
                display = match.group("link_display") if match.group("link_display") is not None else ""
                target  = match.group("link_target") or match.group("link_inner")
                return LinkNode(
                    node_id=self._next_id(),
                    display=display,
                    children=self.parse_content(target, self._patterns.build_node_content_pattern()) if target else []) 
            case "variable":
                match = params["match"]
                prefix = match.group("var_prefix")
                name = match.group("var_name")
                scope = "global_prefix" if prefix == self.format_def.variables.global_prefix else "local_prefix"
                return VariableNode(
                    node_id=self._next_id(),
                    name=name,
                    scope=scope
                )
            case "macro":
                macro_type = params["macro_type"]
                children = params["children"]
                hook = params["hook"] if "hook" in params else None
                return MacroNode(
                    node_id=self._next_id(),
                    macro_type=macro_type,
                    children=self.parse_content(children, self._patterns.build_node_content_pattern()) if children else [],
                    hook=HookNode(
                        node_id=self._next_id(),
                        children=self.parse_content(hook, self._patterns.build_node_content_pattern()) if hook else []
                    ) if hook else None
                )
            case "html":
                tag = params["tag"]
                body = params["body"]
                return HTMLNode(
                    node_id=self._next_id(),
                    tag=tag,
                    body=body
                )
            case "operator":
                match = params["match"]
                return OperatorNode(
                    node_id=self._next_id(),
                    operator=match.group(0)
                )
            case "meta":
                match = params["match"]
                return MetaNode(
                    node_id=self._next_id(),
                    kind=match.group("meta_prefix"),
                    raw=match.group("meta_content")
                )
            case "literal":
                match = params["match"]
                return LiteralNode(
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case "formatting":
                match = params["match"]
                return FormattingNode(
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case _:
                raise ParsingError([f"Unknown node type: {kind}"])
        
        
    def parse_story(self) -> None:
        passages = split_passage(self.document)
        for passage in passages:
            passage_metadata = self.parse_passage_first_line(passage)
            if passage_metadata["title"] is None:
                raise ParsingError([f"Passage missing first line: {passage[:30]}..."])
            if passage_metadata["title"] == "StoryTitle":
                self.story_title = passage_metadata["body"].strip().splitlines()[0].strip()
                continue
            try:
                self.story.passages.append(self.parse_passage(passage_metadata))
            except ParsingError as e:
                raise ParsingError([f"Error parsing passage '{passage_metadata['title']}':"] + e.errors)
        self.story.title = self.story_title
        self.story.format = self.format_def
        self.story.format_version = self.format_def.version


    def parse_passage(self, content_dict: dict) -> Passage:
        if content_dict["title"] is None:
            raise ParsingError([f"Passage missing first line: {content_dict['body'][:30]}..."])
        title = content_dict["title"]
        tags = content_dict["tags"] or ""
        metadata = content_dict["metadata"] or ""
        children = self.parse_content(content_dict["body"], self._patterns.build_passage_content_pattern()) if content_dict["body"] else []
        return Passage(
            node_id=self._next_id(),
            title=title,
            tags=tags,
            metadata=metadata,
            children=children
        )
        
        
    def parse_passage_first_line(self, text: str) -> dict:
        pattern = re.compile(PASSAGE_FIRST_LINE_PATTERN)
        match = pattern.search(text)
        return {
                "title": match.group("title") if match else "",
                "tags": match.group("tags") if match else "",
                "metadata": match.group("metadata") if match else "",
                "body": text[match.end():] if match else ""
        }
        
        
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
            node = self._build_node(args_builder)
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

    
def split_passage(text: str):
    text = textwrap.dedent(text)
    if "::" in text and "\n" not in text:
        raise ParsingError([
            "The file does not contain newline characters. "
            "The Twee file may have been flattened into a single line."
        ])
    passage_cut = re.compile(r"(?=^\s*::)", re.MULTILINE)
    return [passage for passage in passage_cut.split(text) if passage.strip()]

    
    
def story_parsing(text: str, format_def: FormatDefinition) -> tuple[Story, int]:
    parser = Parser(format_def)
    passages = Parser.split_passage(text)
    return parser.parse_story(passages)
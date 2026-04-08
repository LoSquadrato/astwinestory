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
                    children=self.parse_content(target, 
                        self._patterns.build_node_content_pattern())
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
                    children=self.parse_content(children, 
                        self._patterns.build_node_content_pattern())
                )
            case "operator":
                return OperatorNode(
                    node_id=self._next_id(),
                    operator=match.group(0)
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
            format=self.format_def.name,
            format_version=self.format_def.version,
            passages=passages
        )


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
        
    def matching_node_type(self, match) -> str | None:
        if match is None:
            return None
        for key in self._patterns.available():
            if key in match.groupdict() and match.group(key) is not None:
                return key
        return None
    
    # deprecated for refactoring, keeping for reference
    def iterate_content(self, text: str, pattern: re.Pattern):
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        for match in pattern.finditer(text):
            kind = self.matching_node_type(match)
            if kind is None:
                raise ParsingError([f"Regex match missing group: {match}"])
            if kind == "macro":
                macro_content = self.extract_macro_content(text, match.start())
                match = self.get_macro_match(macro_content)
            yield kind, match
      

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
                nodes.append(TextNode(node_id=self._next_id(), value=raw_text))
                pivot = match.end()
            kind = self.matching_node_type(match)
            if kind is None:
                raise ParsingError([f"Regex match missing group: {match}"])
            if kind == "macro":
                start = match.start()
                macro_content = self.extract_macro_content(text, start)
                match = self.get_macro_match(macro_content)
                node = self._build_node(kind, match)
                nodes.append(node)
                pivot = start + len(macro_content)
            else:
                node = self._build_node(kind, match)
                nodes.append(node)
                pivot = match.end()
        if pivot < len(text):
            nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:]))
        return nodes
        
        
    def match_passage_first_line(self, text: str) -> re.Match | None:
        pattern = self._patterns.build_title_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        match = pattern.search(text)
        if match:
            return match 
        return None      


    def extract_macro_content(self, text: str, start: int) -> str | None:
        pattern = self._patterns.build_macro_iteration_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        stack = 0
        for match in pattern.finditer(text, pos=start):
            char = match.group()
            if char == self.format_def.macros.open:
                stack += 1
            elif char == self.format_def.macros.close:
                stack -= 1
                if stack == 0:
                    return text[start:match.end()]
        raise ParsingError([f"Unmatched macro starting at position {start}"])
    
    def get_macro_match(self, text: str) -> re.Match | None:
        pattern = self._patterns.build_macro_with_stack_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        return pattern.match(text)

    # deprecated for refactoring, keeping for reference
    def match_macro_with_stack(self, text: str, start: int) -> re.Match:
        pattern = self._patterns.build_macro_iteration_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        stack = 0
        for match in pattern.finditer(text, pos=start):
            char = match.group()
            if char == self.format_def.macros.open:
                stack += 1
            elif char == self.format_def.macros.close:
                stack -= 1
                if stack == 0:
                    end = match.end()
                    macro_text = text[start:end]
                    # now we have the full macro text, how we can parse it if we can't use
                    # regex to match it?
                    macro_pattern = self._patterns.build_macro_with_stack_pattern()
                    if macro_pattern is None:
                        raise ParsingError(["No macro pattern available for this format definition"])
                    macro_match = macro_pattern.match(macro_text)
                    if not macro_match:
                        raise ParsingError([f"Failed to match macro content: {macro_text}"])
                    return macro_match
        raise ParsingError([f"Unmatched macro starting at position {start}"])
    
    
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
    
    
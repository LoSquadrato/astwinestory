import re
import textwrap
from itertools import count


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
    HookNode,
    MacroNode
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

    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, kind: str, match) -> Node:
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
                raise ParsingError(["Macro nodes should be built using MacroParser, not _build_node."])
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
                    value=match.group("literal")
                )
            case "formatting":
                return FormattingNode(
                    node_id=self._next_id(),
                    value=match.group("formatting")
                )
            case _:
                raise ParsingError([f"Unknown node type: {kind}"])
            
    
    def _matching_node_type(self, match) -> str | None:
        if match is None:
            return None
        for key in self._patterns.available():
            if key in match.groupdict() and match.group(key) is not None:
                return key
        return None 
        
    
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
            kind = self._matching_node_type(match)
            if kind is None:
                raise ParsingError([f"Regex match missing group: {match}"])
            if kind == "macro":
                node, length = self.build_macro_node(text, match.start())
                nodes.append(node)
                pivot = match.start() + length
            else:
                node = self._build_node(kind, match)
                nodes.append(node)
                pivot = match.end()
        if pivot < len(text):
            nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:]))
        # define macro groups for parsing macro's hook or macro content       
        return self.filter_node_list(nodes) 
          
    
        
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
    
    
    def build_macro_node(self, text: str, start: int) -> tuple[MacroNode, int]:
        full_macro_content = self._extract_macro_content(text, start)
        full_macro_match = self._get_macro_match(full_macro_content)
        macro_type = full_macro_match.group("macro_type")
        macro_inner = full_macro_match.group("macro_inner")
        macro_node = MacroNode(
            node_id=self._next_id(),
            macro_type=macro_type,
            children=self.parse_content(macro_inner, self._patterns.build_node_content_pattern())
        )
        return macro_node, len(full_macro_content)
    
    def _extract_macro_content(self, text: str, start: int) -> str | None:
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
    
    def _get_macro_match(self, text: str):
        pattern = self._patterns.build_macro_with_stack_pattern()
        if pattern is None:
            raise ParsingError(["No patterns available for this format definition"])
        return pattern.match(text)
    
    
    def filter_node_list(self, nodes: list[Node]) -> list[Node]:
        if not nodes:
            return []
        transformed_nodes = []
        counter = 0
        while counter < len(nodes):
            node = nodes[counter]
            if node is None or not isinstance(node, Node):
                raise ParsingError("Node in nodes list must be a valid Node instance.")
            if isinstance(node, MacroNode):
                macro_group = self._extract_macro_hook(nodes[counter :])
                transformed_nodes.extend(macro_group)
                counter += len(macro_group)
            else:
                transformed_nodes.append(node)
                counter += 1
        return transformed_nodes

    def _extract_macro_hook(self, node_list: list[Node]) -> list[Node]:
        syntax_type = self.format_def.syntaxtype
        if syntax_type == "markup":
            return self.markup_hook_extraction(node_list)
        elif syntax_type == "linear":
            return self.linear_hook_extraction(node_list)
        else:
            raise ParsingError([f"Unsupported syntax type: {syntax_type}"])  
        
    def markup_hook_extraction(self, node_list: list[Node]) -> list[Node]:
        hook_content = []
        open_macro = node_list[0]
        for node in node_list[1:]:
            if isinstance(node, MacroNode) and node.macro_type == self.format_def.macros.close_tag + open_macro.macro_type:
                hook_node = HookNode(
                    node_id=self._next_id(),
                    hooked_macro_id=open_macro.node_id,
                    children=hook_content
                )
                return [open_macro, hook_node]
            hook_content.append(node)
        raise ParsingError([f"No closing macro found for macro type '{open_macro.macro_type}' with id {open_macro.node_id}"])
    
    def linear_hook_extraction(self, node_list: list[Node]) -> list[Node]:
        macro = node_list[0]
        hook = node_list[1]
        if isinstance(hook, MetaNode):
            parsed_hook = HookNode(
                node_id=hook.node_id,
                hooked_macro_id=macro.node_id,
                children=self.parse_content(hook.raw, self._patterns.build_node_content_pattern())
            )
            return [macro, parsed_hook]
        else:
            raise ParsingError([f"Expected MetaNode as hook after macro, got {type(hook)}"])
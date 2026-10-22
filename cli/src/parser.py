# Simplified parser for story formats
# - add story field which contains the overall story structure
# - export the split passage function, parser has to only parse the passage content
# - 

from enum import Enum
import json
import regex as re
import textwrap
from itertools import count
from dataclasses import dataclass

from .format_definition import FormatDefinition
from .node import (
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

################################################################################################################
# RegexBuilder class is responsible for constructing regex patterns for different components 
# of the story format based on the provided FormatDefinition.
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
            "link":            self._build_link_pattern,
            "operator":        self._build_operator_pattern,
            "literal":         self._build_literal_pattern,
            "formatting":      self._build_formatting_pattern,
            "meta":            self._build_meta_pattern,
            "html":            self._build_html_pattern,
            "quote":           self._build_quoted_string_pattern
        }
        for key, builder in builders.items():
            pattern = builder()
            if pattern is not None:
                self._patterns[key] = pattern
        # build custom patterns from model_extra field, if any and add them to the patterns dict
        # self._patterns.update(self._build_custom_patterns())


    def get_pattern(self, key: str) -> re.Pattern | None:
        return self._patterns.get(key, None)

    # watcher method for available patterns, used in content parser to check if a pattern is available before trying to match it
    def available(self) -> list[str]:
        return list(self._patterns.keys())
       
    # Build variable pattern based on format definition: 
    # define 2 groups for prefix and variable name
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
        return re.compile(rf'(?P<var_prefix>{"|".join(prefixes)})(?P<var_name>\w+)')

# TODO: update macro pattern to handle stack style parsing for nested macros:
# MACRO_START = re.compile(rf'{re.escape(op)}(?P<macro_type>\w[\w-]*:?)')
# TODO: add an escaped character ignore method

    # Build macro pattern based on format definition: 
    # define 3 groups for macro type, inner content, and surrounding delimiters
    def _build_macro_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros:
            return None
        op = self._fmt.macros.open
        cl = self._fmt.macros.close
        if not op or not cl:
            return None
        return re.compile(
                rf'{re.escape(op)}(?P<macro_type>\w[\w-]*:?)\s*(?P<macro_inner>.*?){re.escape(cl)}',
                re.DOTALL
            )   
    
    # Build link pattern based on format definition: 
    # define groups for link display, target, and inner content
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
                rf'({escaped_op})'
                rf'(?:(?P<link_display>.+?)(?:{sep_pattern})(?P<link_target>.+?)'
                rf'|(?P<link_inner>[^{re.escape(cl[0])}]+?))'
                rf'({escaped_cl})',
                re.DOTALL
            )
        else:
            return re.compile(
                rf'({escaped_op})(?P<link_inner>[^{re.escape(cl[0])}]+?)({escaped_cl})',
                re.DOTALL
            )
          
            
    # TODO: operator whose find in macro with text like (go-to: "16 More Ways to Kill a Vampire"),
    # Add an escape for words inside double quotes
    # Build operator pattern based on format definition: 
    # define a group for each operator
    def _build_operator_pattern(self) -> re.Pattern | None:
        if not self._fmt.operators:
            return None
        opts = sorted(
            (opt for opts in self._fmt.operators.values() for opt in opts),
            key=len, reverse=True
        )
        if not opts:
            return None
        return re.compile(r'|'.join(re.escape(opt) for opt in opts))


    # Build literal pattern based on format definition: 
    # define a group for each literal
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



    # Build formatting pattern based on format definition: 
    # define a group for each formatting token
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


    # Build meta pattern based on format definition: 
    # define a group for each meta token
    def _build_meta_pattern(self) -> re.Pattern | None:
        if not self._fmt.meta:
            return None
        pairs = [
            (re.escape(tokens[0]), re.escape(tokens[1]))
            for tokens in self._fmt.meta.values()
            if len(tokens) >= 2 and tokens[0] and tokens[1]
        ]
        if not pairs:
            return None

        delimiter_pattern = "(?:" + "|".join(sorted(
            {token for pair in pairs for token in pair},
            key=len,
            reverse=True
        )) + ")"
        quote_patterns = [
            rf'{re.escape(tokens[0])}(?:\\[\s\S]|(?!{re.escape(tokens[0])})[\s\S])*{re.escape(tokens[0])}'
            for tokens in self._fmt.quote.values()
            if tokens and tokens[0]
        ]
        body_parts = [r"(?&balanced_meta)"]
        if quote_patterns:
            body_parts.append("(?:" + "|".join(quote_patterns) + ")")
        body_parts.append(rf"(?!{delimiter_pattern})[\s\S]")
        body = "(?:" + "|".join(body_parts) + ")*"
        pair_patterns = [f"{opener}{body}{closer}" for opener, closer in pairs]
        return re.compile(
            rf"(?P<balanced_meta>(?:{'|'.join(pair_patterns)}))",
            re.DOTALL
        )
        
        
    # Build HTML pattern based on format definition: 
    # define groups for HTML tag and surrounding delimiters
    def _build_html_pattern(self) -> re.Pattern | None:
        if not self._fmt.html:
            return None
        op = self._fmt.html.open
        cl = self._fmt.html.close
        if not op or not cl:
            return None
        return re.compile(
            rf'{re.escape(op)}(?P<html_tag>\w[\w-]*:?)\s*{re.escape(cl)}',
            re.DOTALL
        )
        
    def _build_quoted_string_pattern(self) -> re.Pattern | None:
        if not self._fmt.quote:
            return None
        delimiters = [re.escape(tokens[0]) for tokens in self._fmt.quote.values()]
        delimiter_pattern = "|".join(delimiters)
        if not delimiter_pattern:
            return None
        return re.compile(
            rf'(?P<quote_delimiter>{delimiter_pattern})(?P<quote_content>.*?)(?P=quote_delimiter)',
            re.DOTALL
        )
 
##############################################################################################
# Story parsing classes and error handling.
# Story data structures.
@dataclass
class Story:
    title:          str
    format:         FormatDefinition
    format_version: str
    passages:       list[Passage]
    
# Regex pattern to identify and regroup the first line of a passage, including its title, tags, and metadata.
PASSAGE_PATTERN = re.compile(
            r'^::\s*(?P<title>[^\[\]{}\n]+?)\s*'
            r'(?:\[(?P<tags>[^\]]*)\])?\s*'
            r'(?:\{(?P<metadata>[^\}]*)\})?\s*$',
            re.MULTILINE
        )  

# Keys used to identify different types of content within a passage. 
# These are used to determine which regex pattern to apply when parsing the passage content.
PASSAGE_CONTENT_KEYS = ["macro", "link", "meta", "html", "variable", "formatting", "quote"]
MACRO_CONTENT_KEYS = ["variable", "operator", "literal", "quote"]
LINK_CONTENT_KEYS = ["variable"]
METADATA_CONTENT_KEYS = ["macro", "meta", "variable", "formatting", "quote"]

class ParsingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ParsingError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        
class Parser:
    def __init__(self, format_def: FormatDefinition, passages: list[str]):
        self._fmt = format_def
        self._passages = passages
        self._counter = count(1)
        self._patterns = RegexBuilder(format_def)
        self.story_title = ""
        self.parsed_passages = []
         # Raw document content to be parsed it can be used in case of big data buffering?
        # self._build = Builder() -- da valutare, potrebbe tornare utile
        
    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, match : re.Match) -> Node:
        node_type = self._get_node_type_from_match(match)
        match node_type:
            case "link":
                display = match.group("link_display") if match.group("link_display") is not None else ""
                target  = match.group("link_target") or match.group("link_inner")
                return LinkNode(
                    node_id=self._next_id(),
                    node_type=node_type,
                    display=display,
                    children=self.parse_content(target, self.build_pattern(LINK_CONTENT_KEYS)) if target else []) 
            case "variable":
                prefix = match.group("var_prefix")
                name = match.group("var_name")
                scope = "global_prefix" if prefix == self._fmt.variables.global_prefix else "local_prefix"
                return VariableNode(
                    node_id=self._next_id(),
                    node_type=node_type,
                    name=name,
                    scope=scope
                )
            case "macro":
                macro_type = match.group("macro_type")
                macro_inner = match.group("macro_inner")
                return MacroNode(
                    node_id=self._next_id(),
                    node_type=node_type,
                    macro_type=macro_type,
                    children=self.parse_content(macro_inner, self.build_pattern(MACRO_CONTENT_KEYS)) if macro_inner else [],
                    hook=None
                )
            case "html":
                return HTMLNode(
                    node_id=self._next_id(),
                    node_type=node_type,
                    tag=match.group("html_tag"),
                    body=match.group(0)
                )
            case "operator":
                return OperatorNode(
                    node_type=node_type,
                    node_id=self._next_id(),
                    operator=match.group(0)
                )
            case "meta":
                meta_value = match.group("meta")
                meta_pairs = sorted(
                    (
                        (tokens[0], tokens[1])
                        for tokens in self._fmt.meta.values()
                        if len(tokens) >= 2 and tokens[0] and tokens[1]
                    ),
                    key=lambda pair: len(pair[0]),
                    reverse=True
                )
                meta_pair = next(
                    (
                        pair for pair in meta_pairs
                        if meta_value.startswith(pair[0]) and meta_value.endswith(pair[1])
                    ),
                    None
                )
                if meta_pair is None:
                    raise ParsingError([f"Could not identify meta delimiters: {meta_value}"])
                meta_prefix, meta_suffix = meta_pair
                meta_content = meta_value[len(meta_prefix):-len(meta_suffix)]
                return MetaNode(
                    node_type=node_type,
                    node_id=self._next_id(),
                    kind=meta_prefix,
                    children=self.parse_content(meta_content, self.build_pattern(METADATA_CONTENT_KEYS)) if meta_content else []
                )
            case "literal":
                return LiteralNode(
                    node_type=node_type,
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case "formatting":
                return FormattingNode(
                    node_type=node_type,
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case "quote":
                return TextNode(
                    node_id=self._next_id(),
                    node_type=node_type,
                    value=match.group("quote_content")
                )
            case _:
                raise ParsingError([f"Unknown node type: {node_type}"])
        
        
    def _get_node_type_from_match(self, match: re.Match) -> str | None:
            if match is None:
                return None
            for key in self._patterns.available():
                if key in match.groupdict() and match.group(key) is not None:
                    return key
            return None
        
        
    def parse_story(self) -> None:
        # passages = split_passage(self.document)
        # split passages outer of the parser class
        for passage in self._passages:
            passage_content = self.parse_passage(passage)
            if passage_content["title"] is None:
                raise ParsingError([f"Passage missing first line: {passage[:30]}..."])
            if passage_content["title"] == "StoryTitle":
                self.story_title = passage_content["body"].strip().splitlines()[0].strip()
                continue
            try:
                self.parsed_passages.append(self.build_passage(passage_content))
            except ParsingError as e:
                raise ParsingError([f"Error parsing passage '{passage_content['title']}':"] + e.errors)


    # Build a Passage object from the parsed content dictionary.    
    def build_passage(self, content_dict: dict) -> Passage: 
        regex_pattern = self.build_pattern(PASSAGE_CONTENT_KEYS)
        if not regex_pattern:
            raise ParsingError(["No patterns available for parsing passage content"])
        return Passage(
            node_id=self._next_id(),
            node_type="passage",
            title=content_dict["title"],
            tags=content_dict["tags"] or "",
            metadata=content_dict["metadata"] or "",
            children=self.group_by_children(self.parse_content(content_dict["body"], regex_pattern))
        )
        
    # Parse individual passage from the raw text.
    # Returns a dictionary with keys: title, tags, metadata, and body.   
    def parse_passage(self, text: str) -> dict:
        pattern = PASSAGE_PATTERN
        match = pattern.search(text)
        return {
                "title": match.group("title") if match else None,
                "tags": match.group("tags") if match else None,
                "metadata": match.group("metadata") if match else None,
                "body": text[match.end():] if match else ""
        }
       
    # find matches for macros, links, variables, media pass them to _build_node, 
    # and recursively parse_macro_nodes for macros    
    def parse_content(self, text: str, pattern: re.Pattern) -> list[Node]:
            if not text:
                return []
            nodes = [] 
            pivot = 0
            for match in pattern.finditer(text):
                if match.start() < pivot:
                    continue  
                if match.start() > pivot:
                    nodes.append(TextNode(node_id=self._next_id(), node_type="text", value=text[pivot:match.start()]))
                    pivot = match.start()
                nodes.append(self._build_node(match))
                pivot = match.end()
            if pivot < len(text):
                nodes.append(TextNode(node_id=self._next_id(), node_type="text", value=text[pivot:]))
            return nodes
    
   
    ############################################################################################
    # Regex pattern builders for different content types
    
    def build_pattern(self, keys: list[str]) -> re.Pattern:
            parts = []
            for key in keys:
                pattern = self._patterns.get_pattern(key)
                if pattern is not None:
                    parts.append(f'(?P<{key}>{pattern.pattern})')
            return re.compile(r'|'.join(parts), re.DOTALL)

###############################################################################################
## Grouping macros for nodes based on syntax type (markup or linear)
###############################################################################################

    def group_by_children(self, nodes: list[Node]) -> list[Node]|None:
        pass
        if not nodes:
            return None
        match self._fmt.get_syntaxtype():
            case "markup":
                return self.group_by_markup_nodes(nodes)
            case "linear":
                return self.group_by_linear_nodes(nodes)
        return nodes
    
    def group_by_markup_nodes(self, nodes: list[Node]) -> list[Node]:
            # TODO:Implement markup-specific grouping logic here if needed
            return nodes
            
        
    def group_by_linear_nodes(self, nodes: list[Node]) -> list[Node]:
        formatted_nodes = []
        pivot = 0
        while pivot < len(nodes):
            node = nodes[pivot]
            if isinstance(node, MacroNode) and self._fmt.have_hook(node.macro_type):
                pivot += 1
                next_node = nodes[pivot] if pivot < len(nodes) else None
                if next_node and isinstance(next_node, MetaNode) and next_node.children:
                    node.hook = HookNode(
                        node_id=next_node.node_id, 
                        node_type="hook", 
                        children=self.group_by_linear_nodes(next_node.children)
                        )
                else:
                    raise ParsingError([f"Expected HookNode with children after hook macro {node}, got: {next_node}"])
            formatted_nodes.append(node)
            pivot += 1
        return formatted_nodes

    
def split_passage(text: str):
    text = textwrap.dedent(text)
    if "::" in text and "\n" not in text:
        raise ParsingError([
            "The file does not contain newline characters. "
            "The Twee file may have been flattened into a single line."
        ])
    passage_cut = re.compile(r"(?=^\s*::)", re.MULTILINE)
    return [passage for passage in passage_cut.split(text) if passage.strip()]

def get_story_format(story : str) -> str:
    # extract story data passage via the regex: (?<=:: StoryTitle)[\s\S]*?(?=::)
    story_data_pattern = re.compile(r"(?<=:: StoryData)[\s\S]*?(?=::)")
    match = story_data_pattern.search(story)
    if not match:
        raise ParsingError(["Story has no StoryData passage"])
    data = json.loads(match.group(0))
    if not "format" in data:
        raise ParsingError(["StoryData passage does not contain a 'format' field"])
    return data["format"]

# Simplified parser for story formats
# - add story field which contains the overall story structure
# - export the split passage function, parser has to only parse the passage content
# - 

import re
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
            "hook":            self._build_linear_hook_pattern
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
        return re.compile(r'|'.join(rf'{re.escape(lit)}(\w.*?){re.escape(lit)}' for lit in lits))



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
        opens = []
        closes = []
        for tokens in self._fmt.meta.values():
            opens.append(re.escape(tokens[0]))
            closes.append(re.escape(tokens[1]))
        if not opens or not closes:
            return None
        return re.compile(
            rf'(?P<meta_prefix>{"|".join(opens)})'
            rf'(?P<meta_content>.*?)'
            rf'(?P<meta_suffix>{"|".join(closes)})', re.DOTALL)
        
        
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
        
    # Build linear hook pattern based on format definition: 
    # define groups for hook opener and closer
    def _build_linear_hook_pattern(self) -> re.Pattern | None:
        if not self._fmt.macros:
            return None
        op = self._fmt.macros.hook_open
        cl = self._fmt.macros.hook_close
        if not op or not cl:
            return None
        return re.compile(
                rf"(?P<opener>{re.escape(op)})|(?P<closer>{re.escape(cl)})",
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
PASSAGE_CONTENT_KEYS = ["macro", "html", "link", "variable", "meta", "formatting"]
NODE_CONTENT_KEYS = ["variable", "macro", "html", "meta",  "operator", "literal", "formatting"]

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
    
    """def _build_node(self, params: dict) -> Node:
            kind = params["kind"]
            match kind:
                case "link":
                    match = params["match"]
                    display = match.group("link_display") if match.group("link_display") is not None else ""
                    target  = match.group("link_target") or match.group("link_inner")
                    return LinkNode(
                        node_id=self._next_id(),
                        display=display,
                        children=self.parse_content(target, self.build_pattern(NODE_CONTENT_KEYS)) if target else []) 
                case "variable":
                    match = params["match"]
                    prefix = match.group("var_prefix")
                    name = match.group("var_name")
                    scope = "global_prefix" if prefix == self._fmt.variables.global_prefix else "local_prefix"
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
                    raise ParsingError([f"Unknown node type: {kind}"])"""
    
    def _build_node(self, match : re.Match) -> Node:
        node_type = self._get_node_type_from_match(match)
        match node_type:
            case "link":
                display = match.group("link_display") if match.group("link_display") is not None else ""
                target  = match.group("link_target") or match.group("link_inner")
                return LinkNode(
                    node_id=self._next_id(),
                    display=display,
                    children=self.parse_content(target, self.build_pattern(NODE_CONTENT_KEYS)) if target else []) 
            case "variable":
                prefix = match.group("var_prefix")
                name = match.group("var_name")
                scope = "global_prefix" if prefix == self._fmt.variables.global_prefix else "local_prefix"
                return VariableNode(
                    node_id=self._next_id(),
                    name=name,
                    scope=scope
                )
            case "macro":
                macro_type = match.group("macro_type")
                macro_inner = match.group("macro_inner")
                return MacroNode(
                    node_id=self._next_id(),
                    macro_type=macro_type,
                    children=self.parse_content(macro_inner, self.build_pattern(NODE_CONTENT_KEYS)) if macro_inner else [],
                    hook=None
                )
            case "html":
                return HTMLNode(
                    node_id=self._next_id(),
                    tag=match.group("html_tag"),
                    body=match.group(0)
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
            title=content_dict["title"],
            tags=content_dict["tags"] or "",
            metadata=content_dict["metadata"] or "",
            children=self.parse_content(content_dict["body"], regex_pattern) if content_dict["body"] else []
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
            if pattern is None:
                raise ParsingError(["No patterns available for this format definition"])
            nodes = [] 
            pivot = 0
            for match in pattern.finditer(text):
                if match.start() < pivot:
                    continue  
                if match.start() > pivot:
                    nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:match.start()]))
                    pivot = match.start()
                nodes.append(self._build_node(match))
                pivot = match.end()
            if pivot < len(text):
                nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:]))
            return nodes
    
    def group_by_children(self, nodes: list[Node]) -> list[Node]|None:
        for node in nodes:
            continue
        pass

   
    ############################################################################################
    # Regex pattern builders for different content types
    
    def build_pattern(self, keys: list[str]) -> re.Pattern:
            parts = []
            for key in keys:
                pattern = self._patterns.get_pattern(key)
                if pattern is not None:
                    parts.append(f'(?P<{key}>{pattern.pattern})')
            return re.compile(r'|'.join(parts), re.DOTALL)
        
          
    def build_macro_content_pattern(self) -> re.Pattern | None:
            # after findind a macro start this pattern work with a stack based function 
            # to extract the whole macro content, including nested macros
            if not self._fmt.macros:
                return None
            op = self._fmt.macros.open
            cl = self._fmt.macros.close
            if not op or not cl:
                return None
            if self._fmt.get_syntaxtype() == "markup":
                close_tag = re.escape(self._fmt.macros.close_tag) if self._fmt.macros.close_tag else ""
                macro_type = rf"(?:{close_tag})?\w[\w-]*:?"
                return re.compile(
                    rf"{re.escape(op)}(?P<macro_type>{macro_type})(?:\s+(?P<macro_inner>.*?))?{re.escape(cl)}",
                    re.DOTALL
                )
            if self._fmt.get_syntaxtype() == "linear":
                macro_type = rf"\w[\w-]*:?"
                return re.compile(
                    rf"(?P<opener>{re.escape(op)}{macro_type})|(?P<closer>{re.escape(cl)})",
                    re.DOTALL
                )
            return None
        
    def build_html_content_pattern(self) -> re.Pattern | None:
            # after findind a html start this pattern work with a stack based function 
            # to extract the whole html content, including nested html
            if not self._fmt.html:
                return None
            op = self._fmt.html.open
            cl = self._fmt.html.close
            if not op or not cl:
                return None
            close_tag = re.escape(self._fmt.html.close_tag) if self._fmt.html.close_tag else ""
            html_type = rf"(?:{close_tag})?\w[\w-]*:?"
            return re.compile(
                rf"{re.escape(op)}(?P<html_tag>{html_type})(?:\s+(?P<html_inner>.*?))?{re.escape(cl)}",
                re.DOTALL
            )
        
    def build_hook_content_pattern(self) -> re.Pattern | None:
            return self.build_pattern(["hook"])


    
def split_passage(text: str):
    text = textwrap.dedent(text)
    if "::" in text and "\n" not in text:
        raise ParsingError([
            "The file does not contain newline characters. "
            "The Twee file may have been flattened into a single line."
        ])
    passage_cut = re.compile(r"(?=^\s*::)", re.MULTILINE)
    return [passage for passage in passage_cut.split(text) if passage.strip()]


"""
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
                raise ParsingError([f"Parse content can't matching node type: {match}"])
            node_contents = self.extract_node_contents(kind, match, text[pivot:])
            pivot += node_contents.get("offset", len(match.group(0)))
            nodes.append(self._build_node(node_contents))
        if pivot < len(text):
            nodes.append(TextNode(node_id=self._next_id(), value=text[pivot:]))
        # define macro groups for parsing macro's hook or macro content       
        return nodes
    
    
    def extract_node_contents(self, kind: str, match: re.Match, text: str) -> dict:
        if self._fmt.get_syntaxtype() == "markup" and kind == "macro":
            return self._extractor.get_macro_params_markup(text)
        if self._fmt.get_syntaxtype() == "linear" and kind == "macro":
            return self._extractor.get_macro_params_linear(text)
        if kind == "html":
            return self._extractor.get_html_params(text)
        return {"kind": kind, "match": match}
     
    
#############################################################################
# Method for extracting macro parameters in markup syntax type
#############################################################################
    
    def get_macro_params_markup(self, text: str) -> dict:
        match = self._get_macro(text)
        if not match:
            raise ParsingError([f"Failed to extract macro from text: {text}"])
        macro_type = match.group("macro_type")
        if macro_type is None:
            raise ParsingError([f"Regex match missing group: {match}"])
        children = match.group("macro_inner")
        if self._fmt.have_hook(macro_type):
            hook_content, closer = self._extract_full_markup_macro_content(macro_type, text[match.end():])
            return {
                "offset": match.end() + len(hook_content) + len(closer),
                "kind": "macro", 
                "macro_type": macro_type, 
                "children": children,
                "hook": hook_content
                }
        else:
            return {
                "offset": match.end(),
                "kind": "macro", 
                "macro_type": macro_type, 
                "children": children,
                }
            
    def _extract_full_markup_macro_content(self, opener_type: str, text: str) -> tuple[str, str] | None:
            stack = 1
            for match in self._patterns.build_macro_content_pattern().finditer(text):
                macro_type = match.group("macro_type")
                if macro_type is None:
                    raise ParsingError([f"Regex match missing group: {match}"])
                if macro_type == self._fmt.macros.close_tag + opener_type:
                    stack -= 1
                if macro_type == opener_type:
                    stack += 1
                if stack == 0:
                    return text[:match.start()], match.group(0) 
            raise ParsingError([f"Unmatched macro opener: {opener_type}"])  # No matching closing tag found
    
    
    def _get_macro(self, text: str) -> re.Match | None:
            match = self.build_pattern(["macro"]).match(text)
            return match if match else None
        
    def _get_macro_first_match(self, text: str) -> re.Match | None:
            pattern = self.build_macro_content_pattern()
            if pattern is None:
                return None
            match = pattern.search(text)
            return match
#############################################################################
# Method for linear syntax type
#############################################################################
    
    def get_macro_params_linear(self, text: str) -> dict:
        params = self._get_macro_and_children_params(text)
        pivot = params["pivot"]
        macro_type = params["macro_type"]
        children = params["children"]
        hook = self._get_hook(text[pivot:], macro_type)
        return {
                "offset": pivot + (len(hook) if hook else 0),  # +1 for the hook opener parenthesis
                "kind": "macro", 
                "macro_type": macro_type, 
                "children": children[:-1],  # Exclude the closing tag from children
                "hook": self._strip_hook_parenthesis(hook) if hook else "" 
                }
        
    def _get_macro_and_children_params(self, text: str) -> dict:
        match = self._get_macro_first_match(text)
        if not match:
            raise ParsingError([f"Failed to extract linear macro from text: {text}"])          
        macro_type = (match.group("opener")).strip(self._fmt.macros.open)
        if macro_type is None:
            raise ParsingError([f"Regex match missing group: {match}"])
        pivot = match.end()
        children = self._extract_linear_content_stack(
            text[pivot:], self._patterns.build_macro_content_pattern(), 1)
        pivot += len(children)
        return {"macro_type": macro_type, "children": children, "pivot": pivot}
           
    def _get_hook(self, text: str, macro_type: str) -> re.Match | None:
        if self._fmt.is_control_macro_opener(macro_type):
            return self._extract_linear_control_content(text)
        elif self._fmt.have_hook(macro_type):
            return self._extract_linear_content_stack(text, self._patterns.build_hook_content_pattern(), 0)
        else:
            return ""
        
    def _strip_hook_parenthesis(self, hook: str) -> str:
        if hook.startswith(self._fmt.macros.hook_open) and hook.endswith(self._fmt.macros.hook_close):
            return hook[1:-1]  # Remove the opening and closing parenthesis
        else:
            raise ParsingError([f"Hook does not have proper parenthesis: {hook}"])
     
    def _extract_linear_content_stack(self, text: str, pattern: re.Pattern, stack: int) -> str:
        match_list = list(pattern.finditer(text))
        if not match_list:
            raise ParsingError([f"Failed to extract linear content from text: {text}"])
        for match in match_list:
            if match.groupdict().get("opener"):
                stack += 1
            elif match.groupdict().get("closer"):
                stack -= 1
            if stack == 0:
                return text[:match.end()]
        raise ParsingError([f"Unmatched linear opener"])
        
    
    def _extract_linear_control_content(self, text: str) -> str:
        hook = self._extract_linear_content_stack(text, self._patterns.build_hook_content_pattern(), 0)
        remaining = text[len(hook):]
        next_match = self._get_macro(remaining)
        if next_match is None or not self._fmt.is_control_macro_continue(next_match.group("macro_type")):
            return hook
        else:
            params = self._get_macro_and_children_params(remaining)
        return (
            hook
            + remaining[:params["pivot"]]
            + self._extract_linear_control_content(remaining[params["pivot"]:])
        )

    
#############################################################################
# Method for html content extraction
#############################################################################     
    
    def get_html_params(self, text: str) -> dict:
        match = self._get_html_tag(text)
        if not match:
            raise ParsingError([f"Failed to extract html macro from text: {text}"])
        html_tag = match.group("html_tag")
        if html_tag is None:
            raise ParsingError([f"Regex match missing group: {match}"])
        html_content = self._extract_full_html_content(html_tag, text[match.end():])
        return {
            "offset": len(match.group(0)) + len(html_content),
            "kind": "html", 
            "tag": html_tag, 
            "body": match.group(0) + html_content
            }
    
    def _get_html_tag(self, text: str) -> re.Match | None:
        match = self._patterns.build_pattern(["html"]).match(text)
        return match if match else None
    
    def _extract_full_html_content(self, opener_tag: str, text: str) -> str:
        stack = 1
        for match in self._patterns.build_html_content_pattern().finditer(text):
            html_tag = match.group("html_tag")
            if html_tag is None:
                raise ParsingError([f"Regex match missing group: {match}"])
            if html_tag == self._fmt.html.close_tag + opener_tag:
                stack -= 1
            if html_tag == opener_tag:
                stack += 1
            if stack == 0:
                return text[:match.end()]  # Return the content between opener and closer
        raise ParsingError([f"Unmatched html tag opener: {opener_tag}"])  # No matching closing tag found
    
    
########################################################################################
# Methods for extracting hook, named hook, hidden hook, unclosed hook from linear syntax
#########################################################################################
"""
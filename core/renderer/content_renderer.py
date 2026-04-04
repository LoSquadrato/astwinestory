import re
import textwrap
from dataclasses import dataclass
from itertools import count
from typing import List
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


class RenderingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "RenderingError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        
        
class Renderer:
    def __init__(self, story: Story):
        self.story = story
        

    def render_node(self, content: List) -> str:
        if len(content) == 0:
            return ""
        for node in content:
            match node:
                case TextNode():
                    return node.value
                case VariableNode():
                    return node.scope + node.name
                case MacroNode():
                    if self.story.format.syntax == "markup":
                        return self.render_markup_macro(node)
                    if self.story.format.syntax == "linear":
                        return self.render_linear_macro(node)
                case LinkNode():
                    open = self.story.format.links.open
                    close = self.story.format.links.close
                    if self.story.format.links.display == "":
                        return f"{open}{self.render_node(node.children)}{close}\n"
                    separator = self.story.format.links.separator[0] 
                    # TODO: support multiple separators
                    # Placeholder for link rendering logic
                    return f"{open}{node.display}{separator}{self.render_node(node.children)}{close}\n"
                case OperatorNode():
                    return node.operator
                case MetaNode():
                    open = self.story.format.macros[node.kind][0]
                    close = self.story.format.macros[node.kind][1]
                    return f"{open}{node.raw}{close}"
                case LiteralNode():
                    return node.value
                case FormattingNode():
                    return node.value
                case _:
                    return RenderingError(f"Unknown node type: {type(node)}")   
                  
    
    def render_story(self, story: Story):
        renderer_story = ""
        for passage in story.passages:
            renderer_story += self.render_passage(passage)
        return renderer_story
    
    def render_passage(self, passage: Passage) -> str:
        renderer_passage = f":: {passage.name} {passage.tags} {passage.metadata}\n"
        return renderer_passage + self.render_node(passage.children) + "\n\n"
    
    def render_markup_macro(self, macro: MacroNode) -> str:
        op = self.story.format.macros.open
        cl = self.story.format.macros.close
        cl_tag = self.story.format.macros.close_tag
        open_macro = f"{op}{macro.macro_type}{cl}"
        close_macro = f"{op}{cl_tag}{macro.macro_type}{cl}"
        return f"{open_macro}{self.render_node(macro.children)}{close_macro}\n"
    
    def render_linear_macro(self, macro: MacroNode) -> str:
        open_macro = self.story.format.macros.open
        close_macro = self.story.format.macros.close
        return f"{open_macro}{macro.macro_type}{self.render_node(macro.children)}{close_macro}\n"
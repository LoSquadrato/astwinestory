from typing import List
from node import (
    Passage,
    TextNode,
    VariableNode,
    MacroNode,
    LinkNode,
    OperatorNode,
    MetaNode,
    LiteralNode,
    FormattingNode,
    HTMLNode,
    HookNode,
)


class RenderingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "RenderingError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        
        
class Render:
    def __init__(self, story: Story):
        self.story = story
        

    def _render_node(self, content: List | HookNode | None) -> str:
        if isinstance(content, HookNode):
            content = content.children
        if content is None:
            return ""
        if len(content) == 0:
            return ""
        nodes = ""
        for node in content:
            match node:
                case TextNode():
                    nodes += node.value
                case VariableNode():
                    nodes += self._render_variable(node)
                case MacroNode():
                    nodes += self._render_macro(node)
                case LinkNode():
                    nodes += self._render_link(node)
                case OperatorNode():
                    nodes += node.operator
                case MetaNode():
                    nodes += self._render_meta(node)
                case LiteralNode():
                    nodes += node.value
                case FormattingNode():
                    nodes += node.value
                case HTMLNode():
                    nodes += node.body
                case _:
                    raise RenderingError([f"Unknown node type: {type(node)}"])
        return nodes   
                  
    
    def _render_story(self, story: Story):
        renderer_story = ""
        if story.title:
            renderer_story += f":: StoryTitle\n{story.title}\n\n"
        for passage in story.passages:
            renderer_story += self._render_passage(passage)
        return renderer_story
    
    def _render_passage(self, passage: Passage) -> str:
        name = passage.name
        tags = f"[{passage.tags}]" if passage.tags else ""
        metadata = f"{{{passage.metadata}}}" if passage.metadata else ""
        renderer_passage = f":: {name} {tags} {metadata}\n"
        return renderer_passage + self._render_node(passage.children) + "\n\n"
    
    def _render_macro(self, macro: MacroNode) -> str:
        if self.story.format.syntaxtype == "markup":
            return self._render_macro_markup(macro)
        elif self.story.format.syntaxtype == "linear":
            return self._render_macro_linear(macro)
        else:
            raise RenderingError([f"Unknown syntax type: {self.story.format.syntaxtype}"])
    
    def _render_macro_markup(self, macro: MacroNode) -> str:
        macros = self.story.format.macros
        if macros is None:
            raise RenderingError(["Macro rendering requires a macro definition"])
        op = macros.open
        cl = macros.close
        cl_tag = macros.close_tag
        ch = self._render_node(macro.children)
        hk = self._render_node(macro.hook) if macro.hook else ""
        if self.story.format.have_hook(macro.macro_type):
            return f"{op}{macro.macro_type} {ch}{cl}{hk}{op}{cl_tag}{macro.macro_type}{cl}"
        return f"{op}{macro.macro_type} {ch}{cl}"
    
    def _render_macro_linear(self, macro: MacroNode) -> str:
        macros = self.story.format.macros
        if macros is None:
            raise RenderingError(["Macro rendering requires a macro definition"])
        op = macros.open
        cl = macros.close
        ch = self._render_node(macro.children)
        hk = self._render_node(macro.hook) if macro.hook else ""
        return f"{op}{macro.macro_type}{ch}{cl}{hk}"
    
    def _render_link(self, link: LinkNode) -> str:
        op = self.story.format.links.open
        cl = self.story.format.links.close
        if link.display == "":
            return f"{op}{self._render_node(link.children)}{cl}"
        separator = self.story.format.links.separators[0]
        return f"{op}{link.display}{separator}{self._render_node(link.children)}{cl}"
    
    def _render_variable(self, variable: VariableNode) -> str:
        prefix = getattr(self.story.format.variables, variable.scope)
        return f"{prefix}{variable.name}"
    
    def _render_meta(self, meta: MetaNode) -> str:
        tokens = self.story.format.get_meta_tokens(meta.kind)
        if not tokens:
            raise RenderingError([f"Unknown meta kind: {meta.kind}"])
        open, close = tokens
        return f"{open}{meta.raw}{close}"

    
def story_rendering(story: Story) -> str:
    render = Render(story)
    return render._render_story(story)
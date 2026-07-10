from config import TEXT_EXCAPE_KEY
from core.ast import (
    Story, 
    Passage, 
    Node,
    TextNode,
    VariableNode,
    MacroNode,
    LinkNode,
    OperatorNode,
    MetaNode,
    LiteralNode,
    FormattingNode,
    HookNode
)

class ExtractorError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ExtractorError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)

class Extractor:
    def __init__(self):
         self.escaped = TEXT_EXCAPE_KEY
         
    def extract_story(self, story: Story) -> str:
        extracted_story = ""
        for passage in story.passages:
            extracted_story += self.extract_passage(passage)
        return extracted_story
    
    def extract_passage(self, passage: Passage) -> str:
        if passage is None:
            raise ExtractorError(["Passage must be provided for extraction."])
        name = passage.name
        tags = f"{self.escaped}{passage.tags}{self.escaped}" if passage.tags else ""
        metadata = f"{self.escaped}{passage.metadata}{self.escaped}" if passage.metadata else ""
        extracted_passage = f":: {self.escaped}{passage.node_id}{self.escaped} {name} {tags} {metadata}\n"
        return extracted_passage + self.render_node(passage.children) + "\n\n"
    
    def extract_content(self, content: list[Node]) -> str:
        if len(content) == 0:
            return ""
        extracted_content = ""
        for node in content:
            match node:
                case TextNode():
                    extracted_content += node.value
                case VariableNode():
                    extracted_content += f"{self.escaped}{node.node_id}{self.escaped}"
                case MacroNode():
                    extract_children = self.extract_content(node.children)
                    extracted_content += f"{self.escaped}{node.node_id}({extract_children}){self.escaped}"
                case LinkNode():
                    extract_children = self.extract_content(node.children)
                    extracted_content += f"{self.escaped}{node.node_id} -> {node.display} | {extract_children}{self.escaped}"
                case OperatorNode():
                    extracted_content += f"{self.escaped}{node.node_id}{self.escaped}"
                case MetaNode():
                    extracted_content += f"{self.escaped}{node.node_id}{self.escaped}"
                case LiteralNode():
                    extracted_content += f"{self.escaped}{node.node_id}{self.escaped}"
                case FormattingNode():
                    extracted_content += f"{self.escaped}{node.node_id}{self.escaped}"
                case HookNode():
                    extract_children = self.extract_content(node.children)
                    extracted_content += f"{self.escaped}{node.node_id}({extract_children}){self.escaped}"
                case _:
                    raise ExtractorError([f"Unknown node type: {type(node)}"])
        return extracted_content
    
def text_extractor(story: Story) -> str:
    extractor = Extractor()
    return extractor.extract_story(story)
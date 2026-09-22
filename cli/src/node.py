from dataclasses import dataclass

@dataclass
class Node:
    node_id: int

@dataclass
class TextNode(Node):
    value: str
    
@dataclass
class VariableNode(Node):
    name: str 
    scope: str  # "global" or "local"
    
@dataclass
class HookNode(Node):
    children: list[Node]
    
# container for macro's hook and content  
@dataclass
class MacroNode(Node):
    macro_type: str
    children: list[Node] | None = None  # Optional children nodes for macro content
    hook: HookNode | None = None  # Optional hook node for macro content

@dataclass
class LinkNode(Node):
    display: str = ""
    children: list[Node]| None = None
    
@dataclass
class OperatorNode(Node):
    operator: str

@dataclass
class MetaNode(Node):
    kind: str
    raw: str 
    
@dataclass
class HTMLNode(Node):
    tag: str
    body: str = ""
    
@dataclass
class LiteralNode(Node):
    value: str
    
@dataclass
class FormattingNode(Node):
    value: str

@dataclass
class Passage(Node):
    title:        str
    tags:        str
    metadata:    str 
    children:    list[Node] | None = None  # Optional children nodes for passage content
from dataclasses import dataclass, field


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
class MacroNode(Node):
    macro_type: str
    children: list[Node] = field(default_factory=list)

@dataclass
class LinkNode(Node):
    display: str = ""
    children: list[Node] = field(default_factory=list)
    
@dataclass
class OperatorNode(Node):
    operator: str

@dataclass
class MetaNode(Node):
    kind: str
    raw: str
    
@dataclass
class LiteralNode(Node):
    value: str
    
@dataclass
class FormattingNode(Node):
    value: str
    
    
@dataclass
class Passage(Node):
    name:        str
    tags:        str
    metadata:    str
    children:    list[Node] = field(default_factory=list)



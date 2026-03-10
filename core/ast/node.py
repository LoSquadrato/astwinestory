from dataclasses import dataclass, field
from enum import Enum
from typing import List


@dataclass
class Node:
    node_id: int

# eliminare perchè ormai non serve più
@dataclass
class NodeType(Enum):
    PASSAGE = "passage"
    MACRO = "macro"
    LINK = "link"
    VARIABLE = "variable"
    TEXT = "text"
    OPERATOR = "operator"
    META = "meta"

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
    target: str
    
@dataclass
class OperatorNode(Node):
    operator: str

@dataclass
class MetaNode(Node):
    kind = str
    raw: str
    
@dataclass
class Passage(Node):
    name:        str
    children:    list[Node] = field(default_factory=list)



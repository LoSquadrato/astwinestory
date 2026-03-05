from dataclasses import dataclass, field
from enum import Enum
from typing import List


@dataclass
class Node:
    node_id: int

@dataclass
class NodeType(Enum):
    PASSAGE = "passage"
    MACRO = "macro"
    LINK = "link"
    VARIABLE = "variable"
    TEXT = "text"
    OPERATOR = "operator"
    META = "meta"


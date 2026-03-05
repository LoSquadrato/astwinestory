from dataclasses import dataclass, field
from typing import List
from .node import Node

@dataclass
class MacroNode(Node):
    macro_type: str
    children:   list[Node] = field(default_factory=list)

    
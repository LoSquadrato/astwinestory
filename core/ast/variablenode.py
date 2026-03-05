from dataclasses import dataclass
from .node import Node

@dataclass
class VariableNode(Node):
    name: str
    scope: str  # "global" or "local"
from dataclasses import dataclass, field
from typing import List
from .node import Node

@dataclass
class LinkNode(Node):
    display: str
    target:  str

    
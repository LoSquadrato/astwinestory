from dataclasses import dataclass
from typing import List
from .node import Node

@dataclass   
class TextNode(Node):
    value: str
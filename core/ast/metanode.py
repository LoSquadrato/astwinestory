from dataclasses import dataclass, field
from typing import List
from .node import Node

@dataclass   
class MetaNode(Node):
    raw: str
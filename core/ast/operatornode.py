from dataclasses import dataclass, field
from enum import Enum
from typing import List
from .node import Node

@dataclass   
class OperatorNode(Node):
    operator: str

from dataclasses import dataclass, field
from typing import List
from .node import Node

@dataclass
class Passage(Node):
    name:        str
    tags:        list[str]
    children:    list[Node] = field(default_factory=list)


    def add_child(self, child: Node):
        self.children.append(child)



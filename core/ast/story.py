from dataclasses import dataclass

from core.formats import FormatDefinition
from core.ast.node import Passage


@dataclass
class Story:
    title:          str
    format:         FormatDefinition
    format_version: str
    passages:       list[Passage] = []
    
    
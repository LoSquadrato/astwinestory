from dataclasses import dataclass, field

from core.formats.format_definition import FormatDefinition
from .node import Passage


@dataclass
class Story:
    title:          str
    format:         FormatDefinition
    passages:       list[Passage] = field(default_factory=list)
    format_version: str
    
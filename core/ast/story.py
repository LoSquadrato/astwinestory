from dataclasses import dataclass, field

from core.formats.format_definition import FormatDefinition
from .node import Passage


@dataclass
class Story:
    title:          str
    format:         str
    passages:       list[Passage] = field(default_factory=list)
    # optional metadata extracted from StoryData
    ifid:           str | None = None
    format_version: str | None = None
    start_passage:  str | None = None
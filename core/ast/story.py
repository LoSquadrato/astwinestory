from dataclasses import dataclass, field
from .passage import Passage
from core.parser.formats import TweeFormat



@dataclass
class Story:
    title: str
    ifid: str
    format: TweeFormat
    format_version: str
    start_passage: str
    passages: dict[str, Passage] = field(default_factory=dict)
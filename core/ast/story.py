import warnings
from dataclasses import dataclass, field
import uuid
from passage import Passage
from core.parser.formats import TweeFormat, SUPPORTED_FORMAT_VERSIONS
from core.parser.errors import ParsingError


@dataclass
class Story:
    title: str
    ifid: str
    format: TweeFormat
    format_version: str
    start_passage: str
    passages: dict[str, "Passage"] = field(default_factory=dict)

    def __post_init__(self):
        errors = []

        # --- IFID validation ---
        if not self.ifid:
            errors.append("Missing IFID")
        else:
            try:
                uuid.UUID(self.ifid)
            except ValueError:
                errors.append("Invalid IFID (must be a valid UUID)")

        # --- start passage ---
        if not self.start_passage:
            errors.append("Missing start node")

        # --- format version ---
        supported_versions = SUPPORTED_FORMAT_VERSIONS.get(self.format.value)

        if supported_versions is None:
            errors.append(f"Unsupported format '{self.format.value}'")
        elif self.format_version not in supported_versions:
            errors.append(
                f"Unsupported format-version '{self.format_version}' "
                f"for format '{self.format.value}'"
            )

        # --- raise aggregated error ---
        if errors:
            raise ParsingError(errors)

'''
from dataclasses import dataclass, field
from typing import Dict
from .passage import Passage



@dataclass
class Story:
    title:           str
    ifid:            str
    format:          str
    format_version:  str
    start_passage:   str
    passages:        dict[str, Passage] = field(default_factory=dict)
    
    def add_passage(self, passage: Passage):
        self.passages[passage.node_id] = passage
'''
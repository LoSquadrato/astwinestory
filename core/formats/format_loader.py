import json
import os
from core.config import FORMATS_DIR
from core.formats import FormatDefinition
from pydantic import ValidationError as PydanticValidationError


class FormatLoaderError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def load_format(format_name: str) -> FormatDefinition:
    path = _resolve_path(format_name)
    raw  = _read_json(path)
    return _build_definition(raw)


def _resolve_path(format_name: str) -> str:
    normalized = format_name.lower().replace(" ", "_")
    
    formats_dir = os.path.abspath(os.path.join(FORMATS_DIR))

    candidates = [
        os.path.join(formats_dir, f"{normalized}.json"),
        os.path.join(formats_dir, "custom", f"{normalized}.json"),
    ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    raise FormatLoaderError(
        f"Format definition not found for '{format_name}'. "
        f"Searched: {candidates}"
    )


def _read_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FormatLoaderError(f"Invalid JSON in format definition '{path}': {e}")
    except OSError as e:
        raise FormatLoaderError(f"Failed to read format definition '{path}': {e}")


def _build_definition(raw: dict) -> FormatDefinition:
    try:
        return FormatDefinition.model_validate(raw)
    except PydanticValidationError as e:
        raise FormatLoaderError(f"Invalid format definition: {e}") from e
    

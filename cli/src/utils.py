
import os
from pathlib import Path


MAX_STORY_SIZE = 10 * 1024 * 1024  # 10 MB limit for input story

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FORMATS_PATH = os.path.join(PROJECT_ROOT, "assets", "formats")

TEXT_EXCAPE_KEY = "%%"

OUTPUT_DIR = "cache"



def load_story(path: Path):
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Story not found or not a file: {path}")
    size = path.stat().st_size
    if size > MAX_STORY_SIZE:
        raise ValueError(f"Input story exceeds maximum allowed size ({MAX_STORY_SIZE} bytes)")
    with path.open("r", encoding="utf-8") as f:
        raw = f.read()
    return raw

def get_format_list() -> list[str]:
    try:
        formats = [file for file in os.listdir(FORMATS_PATH) if file.endswith(".json")]
    except OSError:
        raise ValueError(f"Invalid path: {FORMATS_PATH}")
    if not formats:
        raise ValueError(f"No formats found in path: {FORMATS_PATH}")
    return [Path(entry).stem for entry in formats]
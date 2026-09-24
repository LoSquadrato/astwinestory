
import os
import json
from pathlib import Path
from dataclasses import asdict


MAX_STORY_SIZE = 10 * 1024 * 1024  # 10 MB limit for input story

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FORMATS_PATH = os.path.join(PROJECT_ROOT, "assets", "formats")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "cache")

TEXT_EXCAPE_KEY = "%%"



def load_story(file_path: str):
    path = Path(file_path)
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

def parsed_passages_to_json(parsed_passages: list, story_title: str) -> None:
    to_json = [asdict(passage) for passage in parsed_passages]
    output_path = os.path.join(OUTPUT_DIR, f"{story_title}_parsed.json")
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(json.dumps(to_json, indent=4))
        print(f"Successfully wrote parsed passages to '{output_path}'.")
    except Exception as e:
        print(f"An error occurred while writing to '{output_path}': {e}")
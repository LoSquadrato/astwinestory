import os

from rich.console import Console
from pathlib import Path
from .menus import select_from_menu, get_format_list
from config import FORMATS_DIR, MAX_STORY_SIZE, SUGGESTED_OUTPUT_DIR

class REPLError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
        

def _validate_output_path(source: Path, name: str) -> Path:
    for p in source.iterdir():
        if p.is_file() and p.stem == name:
            print(f"  File name '{name}' already exists.")
            print(f"  Using new file name: '{name}_1'")
            name = f"{name}_1"
    return os.path.abspath(os.path.join(SUGGESTED_OUTPUT_DIR, f"{name}"))


def _confirm_output_path() -> Path:
    print(f"{'─' * 50}")
    print(f"  Output path:")
    suggested_path = os.path.abspath(SUGGESTED_OUTPUT_DIR)
    print(f"  {suggested_path}")
    print(f"\n{'─' * 50}")
    name = input("  Enter desired file name (without extension): ").strip()
    if not name:
        print("  ✗ Invalid input. File name cannot be empty.")
        return _confirm_output_path()
    if len(name) > 225:
        print("  ✗ Invalid input. File name cannot exceed 225 characters.")
        return _confirm_output_path()
    path = _validate_output_path(SUGGESTED_OUTPUT_DIR, name)
    print(f"{'─' * 50}")
    
    return path

# Validate file exists and size before reading
def file_loader(path: Path) -> str:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Story not found or not a file: {path}")
    size = path.stat().st_size
    if size == 0:
        raise ValueError("Input story is empty")
    if size > MAX_STORY_SIZE:
        raise ValueError(f"Input story exceeds maximum allowed size ({MAX_STORY_SIZE} bytes)")

    with path.open("r", encoding="utf-8") as f:
        raw = f.read()
    if not raw:
        raise ValueError("Unable to read story content")
    return raw


def run_repl(path: Path, console: Console, func_lst: list) -> dict:
    console.print("Welcome to StoryLoom CLI!", style="bold cyan")
    console.print(f"Using story: {path}", style="bold red")
    console.print("Please do not edit stories you do not own or have rights to.", style="bold red")
    
    command = {}

    # ── Step 1: choose output format ───────────────────────────────────────
    command["format"] = select_from_menu(
        "Select output format",
        get_format_list(FORMATS_DIR, format_list=[]),
    )

    # ── Step 2: choose operation ───────────────────────────────────────────
    command["function"] = select_from_menu("Select function", func_lst)
        
    # ── Step 3: confirm / modify output path ───────────────────────────────
    command["output_path"] = _confirm_output_path()

    return command



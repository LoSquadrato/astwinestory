import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List



@dataclass
class MenuOption:
    key: str
    label: str

def _display_menu(title: str, options: Any) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")
    for i, opt in enumerate(options, start=1):
        print(f"  [{i}]  {opt.label}")
    print(f"{'─' * 50}")

def select_from_menu(title: str, options: Any) -> MenuOption:
    while True:
        _display_menu(title, options)
        raw = input("  Choice: ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                selected = options[idx]
                print(f"  ✓ Selected: {selected.label.strip()}")
                return selected
        print(f"  ✗ Invalid input. Enter a number between 1 and {len(options)}.")
        
def get_format_list(path: Path, format_list: List[MenuOption]) -> List[MenuOption]:
    if not path:
        raise ValueError("Path cannot be None or empty")
    try:
        list_dir = os.listdir(path)
    except OSError:
        raise ValueError(f"Invalid path: {path}")
    if not list_dir:
        return format_list
    for entry in list_dir:
        file_path = os.path.join(path, entry)
        if os.path.isfile(file_path):
            name = os.path.basename(file_path).split('.')[0]
            format_list.append(MenuOption(key=name, label=name))
            continue
        if os.path.isdir(file_path):
            get_format_list(Path(file_path), format_list)
    return format_list

        
        
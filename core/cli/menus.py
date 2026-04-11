import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class MenuOption:
    key: str
    label: str


# todo: add func field in MenuOption to call the selected function to make easier to add new functions in the future, 
# and to handle the function execution in a more structured way
FUNCTIONS_LIST = [    
    MenuOption(key="convert", label="Convert variables and macros of a story from one format to another"),
    MenuOption(key="extract", label="Extract the text of a story while keeping macro placeholders"),
    MenuOption(key="render", label="[only for testing] Render the story text, write a file at output path"),
]

def display_menu(title: str, options: List[MenuOption]) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")
    for i, opt in enumerate(options, start=1):
        print(f"  [{i}]  {opt.label}")
    print(f"{'─' * 50}")

def select_from_menu(title: str, options: List[MenuOption]) -> MenuOption:
    while True:
        display_menu(title, options)
        raw = input("  Choice: ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                selected = options[idx]
                print(f"  ✓ Selected: {selected.label.strip()}")
                return selected
        print(f"  ✗ Invalid input. Enter a number between 1 and {len(options)}.")
        
def get_format_list(path: Path, format_list: List[MenuOption]) -> List[MenuOption]:
    """Recursively retrieve available format names from directory and wrap them as MenuOption."""
    if not path:
        return format_list
    try:
        list_dir = os.listdir(path)
    except OSError:
        return format_list
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
            
            
        
        
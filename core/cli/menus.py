import os
from pathlib import Path


FUNCTIONS = [
    "Convert variables and macros of a story from one format to another",
    "Extract the text of a story by keeping placeholders for macros",
    ]

def display_menu(title: str, options: list[str]) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")
    for i, opt in enumerate(options, start=1):
        print(f"  [{i}]  {opt}")
    print(f"{'─' * 50}")

def select_from_menu(title: str, options: list[str]) -> str:
    while True:
        display_menu(title, options)
        raw = input("  Scelta: ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                selected = options[idx]
                print(f"  ✓ Selezionato: {selected.label.strip()}")
                return selected
        print(f"  ✗ Input non valido. Inserisci un numero tra 1 e {len(options)}.")
        
def get_format_list(path : Path, format_list : list[str]) -> list[str]:
    if not path:
        return format_list
    list_dir = os.listdir(path)
    if not list_dir:
        return format_list
    for l in list_dir:
        file_path = os.path.join(path, l)
        if os.path.isfile(file_path):
            name = os.path.basename(file_path).split('.')[0]
            format_list.append(name)
            continue
        if os.path.isdir(file_path):
            get_format_list(file_path, format_list)
    return format_list
            
            
        
        
import os

from rich.console import Console
from pathlib import Path
from core.cli.menus import select_from_menu, get_format_list
from core.config import FORMATS_DIR, MAX_STORY_SIZE, SUGGESTED_OUTPUT_DIR



def _validate_output_path(source: Path, name: str, ext: str) -> str:
    if not source.exists():
        os.makedirs(source)
    for p in source.iterdir():
        if p.is_file() and p.stem == name:
            i = 1
            while True:
                new_name = f"{name}_{i}"
                new_path = source / f"{new_name}{ext}"
                if not new_path.exists():
                    name = new_name
                    break
                i += 1
            print(f"  File name you choose already exist")
            print(f"  Using this file name: {name}{ext}")
    return os.path.abspath(os.path.join(SUGGESTED_OUTPUT_DIR, f"{name}{ext}"))


def _confirm_output_path(ext: str) -> str:
    print(f"{'─' * 50}")
    print(f"  Output path:")
    suggested_path = os.path.abspath(SUGGESTED_OUTPUT_DIR)
    print(f"  {suggested_path}")
    print(f"\n{'─' * 50}")
    name = input("  Enter desired file name (without extension): ").strip()
    if not name:
        print("  ✗ Invalid input. File name cannot be empty.")
        return _confirm_output_path(ext)
    if len(name) > 225:
        print("  ✗ Invalid input. File name cannot exceed 225 characters.")
        return _confirm_output_path(ext)
    path = _validate_output_path(Path(suggested_path), name, ext)
    print(f"{'─' * 50}")
    
    return path


def run_repl(path: Path, console: Console, func_lst: list) -> dict:
    title = r'''
 $$$$$$\    $$\                                   $$\                                        
$$  __$$\   $$ |                                  $$ |                                       
$$ /  \__|$$$$$$\    $$$$$$\   $$$$$$\  $$\   $$\ $$ |      $$$$$$\   $$$$$$\  $$$$$$\$$$$\  
\$$$$$$\  \_$$  _|  $$  __$$\ $$  __$$\ $$ |  $$ |$$ |     $$  __$$\ $$  __$$\ $$  _$$  _$$\ 
 \____$$\   $$ |    $$ /  $$ |$$ |  \__|$$ |  $$ |$$ |     $$ /  $$ |$$ /  $$ |$$ / $$ / $$ |
$$\   $$ |  $$ |$$\ $$ |  $$ |$$ |      $$ |  $$ |$$ |     $$ |  $$ |$$ |  $$ |$$ | $$ | $$ |
\$$$$$$  |  \$$$$  |\$$$$$$  |$$ |      \$$$$$$$ |$$$$$$$$\\$$$$$$  |\$$$$$$  |$$ | $$ | $$ |
 \______/    \____/  \______/ \__|       \____$$ |\________|\______/  \______/ \__| \__| \__|
                                        $$\   $$ |                                           
                                        \$$$$$$  |                                           
                                         \______/                                            
'''
    console.print(title, style="bold cyan")
    console.print(f"Using story: {path}", style="bold red")
    console.print("Please do not edit stories you do not own or have rights to.", style="bold red")
    
    command = {}

    # ── Step 1: choose output format ───────────────────────────────────────
    command["format"] = select_from_menu(
        "Select output format",
        get_format_list(Path(os.path.abspath(FORMATS_DIR)), format_list=[]),
    )

    # ── Step 2: choose operation ───────────────────────────────────────────
    selection = select_from_menu("Select function", [{"key": func.key, "label": func.label} for func in func_lst])
    
    command["function"] = next(func for func in func_lst if func.key == selection.key)
        
    # ── Step 3: confirm / modify output path ───────────────────────────────
    command["output_path"] = _confirm_output_path(command["function"].extension)

    return command




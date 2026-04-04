from rich.console import Console
from pathlib import Path
from .menus import FUNCTIONS_LIST, select_from_menu, get_format_list
from .converter import convert, ConversionError
from core.parser.content_parser import Parser
from core.formats.format_loader import load_format, FORMATS_DIR

console = Console()

MAX_STORY_SIZE = 10 * 1024 * 1024  # 10 MB limit for input story


def _suggest_output_path(source: Path, format: str) -> Path:
    return source.with_stem(f"{source.stem}_{format}")

def _confirm_output_path(suggested: Path) -> Path:
    print(f"\n{'─' * 50}")
    print(f"  Suggested output path:")
    print(f"  {suggested}")
    print(f"{'─' * 50}")
    print("  [Enter] confirm suggested path")
    print("  [path]  type an alternative path")
    print(f"{'─' * 50}")

    raw = input("  Output path: ").strip()

    if raw == "":
        return suggested

    custom = Path(raw)
    # Se l'utente digita solo un nome senza directory, usare la stessa cartella del sorgente
    if not custom.is_absolute() and custom.parent == Path("."):
        custom = suggested.parent / custom

    return custom

def file_loader(path: Path) -> str:
    # validate file exists and size before reading
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


def run_repl(path: Path) -> dict:
    console.print("Welcome to StoryLoom CLI!", style="bold cyan")
    console.print(f"Using story: {path}", style="bold red")
    console.print("Please do not edit stories you do not own or have rights to.", style="bold red")
    
    command = {}

    while True:
        # ── Step 1: choose output format ───────────────────────────────────────
        fmt_option = select_from_menu(
            "Select output format",
            get_format_list(FORMATS_DIR, format_list=[]),
        )
        command["format"] = fmt_option

        # ── Step 2: choose operation ───────────────────────────────────────────
        fn_option = select_from_menu("Select function", FUNCTIONS_LIST)
        command["function"] = fn_option
        

        # ── Step 3: confirm / modify output path ───────────────────────────────
        suggested = _suggest_output_path(path, fmt_option.key)
        output_path = _confirm_output_path(suggested)
        command["output_path"] = output_path

        return command



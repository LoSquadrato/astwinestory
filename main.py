import sys
from rich.console import Console
from pathlib import Path

from command import HANDLERS_LIST, new_command_option, handle_command
from core.cli import file_loader, run_repl
from core.config.config import MAX_STORY_SIZE
from core.src import story_parsing, story_rendering
from core.formats import load_format

# TODO:
# - define builder class to build passage and nodes, and use it in the parser. Parser should make story and parse content
# - function list must contain function objects not MenuOption
# - refactor the pipeline: main.py + input_file -> repl -> input: format, function, output -> handle function -> output_file


def validate_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Invalid or non-existent path: {path}")
    if path.suffix.lower() not in (".twee", ".tw"):
        raise ValueError(f"Invalid file extension '{path.suffix}' (expected .twee or .tw)")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py «path/to/storyfile»")
        sys.exit(1)

    source_path = Path(sys.argv[1])

    # TODO: put all this in a loader.py file, better in a REPL class, and use it in main.py
    try:
        validate_path(source_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    console = Console()
    
    try:
        command = new_command_option(run_repl(source_path, console, HANDLERS_LIST))
    except KeyboardInterrupt:
        print("\n\n  Interrupted by the user.\n")
        sys.exit(1)
    except Exception as e:
        print(f"Error during REPL: {e}")
        sys.exit(1)
        
    print(f"\n  Processing...")
     
    try:
        handle_command(command, file_loader(source_path))
    except Exception as e:
        console.print(f"[red]{e}[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
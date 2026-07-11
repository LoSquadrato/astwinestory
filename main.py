import sys
from rich.console import Console
from pathlib import Path

from core.cli import MenuOption, run_repl, file_loader    
from core.src import story_parsing, story_rendering
from core.formats import load_format

# Functions available in the REPL menu, for adding new functionalities, add a new MenuOption here with the corresponding key, label, and function to execute. 
# Every function should accept a Story object and return a string.
FUNCTIONS_LIST = [    
    # MenuOption(key="convert", label="Convert variables and macros of a story from one format to another"),
    # MenuOption(key="extract", label="Extract the text of a story while keeping macro placeholders", func=text_extractor),
    MenuOption(key="render", label="[only for testing] Render the story text, write a file at output path", func=story_rendering, extension=".twee"),
]

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
        command = run_repl(source_path, console, FUNCTIONS_LIST)
    except KeyboardInterrupt:
        print("\n\n  Interrupted by the user.\n")
        sys.exit(1)
        
    print(f"\n  Processing...")
        
    try:
        parsed_story, _ = story_parsing(
            file_loader(source_path),
            load_format(command["format"].key)
            )
    except Exception as e:
        console.print(f"[red]{e}[/]")
        sys.exit(1)
    console.print("[green]Validation passed.[/]")
    console.print(f"[blue]Title: {parsed_story.title}[/]")
    console.print(f"[blue]Format: {parsed_story.format}[/]")
    console.print(f"[blue]Passages: {len(parsed_story.passages)}[/]")
    
    
    try:
        result = command["function"].func(parsed_story)
    except Exception as e:
        console.print(f"[red]{e}[/]")
        sys.exit(1)
    with open(command["output_path"], "w", encoding="utf-8") as f:
        f.write(result)
    console.print(f"[green]Story rendered and saved to {command['output_path']}[/]")

if __name__ == "__main__":
    main()
    
import sys
from pathlib import Path
from core.cli.run_repl import run_repl, file_loader
from core.parser import Parser, ParsingError, RegexBuilder
from core.formats import load_format, FormatDefinitionError, FormatLoaderError
from rich.console import Console

from core.parser.content_render import Render

console = Console()

'''
FUNCTIONS = {
    "convert": Convert,
    "extract": Extract,
    # "stats": "Generate statistics about the story (e.g. passage count, link count, etc.)"
}
'''

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py «path/to/storyfile»")
        sys.exit(1)

    source_path = Path(sys.argv[1])

    if not source_path.exists():
        print(f"Error: invalid or inexistence path -> {source_path}")
        sys.exit(1)

    if source_path.suffix.lower() not in (".twee", ".tw"):
        print(f"Error: invalid file '{source_path.suffix}' (expected .twee or .tw)")
        sys.exit(1)
    try:
        command = run_repl(source_path)
    except KeyboardInterrupt:
        print("\n\n  Interrupted by the user.\n")
        sys.exit(1)
        
    print(f"\n  Processing...")

    text = file_loader(source_path)
    
    format_definition = load_format(command["format"].key)
        
    parser = Parser(format_definition)
    try:
        parsed_story, next_node_id = parser.parse_story(Parser.split_passage(text))
    except Exception as e:
        console.print(f"[red]{e}[/]")
        sys.exit(1)
    console.print("[green]Validation passed.[/]")
    console.print(f"[blue]Title: {parsed_story.title}[/]")
    console.print(f"[blue]Format: {parsed_story.format}[/]")
    console.print(f"[blue]Passages: {len(parsed_story.passages)}[/]")
    console.print(f"[blue]Last node ID: {last_node_id}[/]")
    
    if command["function"].key == "convert":
        pass
    if command["function"].key == "extract":
        pass
    if command["function"].key == "render":
        render = Render(parsed_story)
        try:
            rendered_story = render.render_story(parsed_story)
        except Exception as e:
            console.print(f"[red]{e}[/]")
            sys.exit(1)
        with open(command["output_path"], "w", encoding="utf-8") as f:
            f.write(rendered_story)
        console.print(f"[green]Story rendered and saved to {command['output_path']}[/]")
    else:
        console.print(f"[red]Unknown function: {command['function'].key}[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
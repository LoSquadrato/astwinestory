from rich.console import Console
from rich.text import Text

console = Console()

def repl():
    text = Text("We love StoryLoom!!", style="bold cyan")
    console.print(text)

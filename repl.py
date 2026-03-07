import sys
import os
from rich.console import Console
from rich.text import Text
#from core.parser.parser import Parser
from core.parser.extract_story import extract_story
#from core.validator.path_validator import path_validator, Exception
#from core.parser.extract_story import extract_story

console = Console()

def repl(path):

    console.print("This is StoryLoom!!", style="bold cyan")
    if path_validator(path):
        try:
            text = file_loader(path)
            story = extract_story(text)
                           
            # se non ci sono errori vado con la seconda parte
                    
        except Exception as e:
            console.print(f"[red]{e}[/]")
            sys.exit(3)
                # for testing, delete message in future
        console.print("[green]Validation passed.[/]")
        print(story)
        # scelta se tradurre in lingua o cambiare formato
        # per la traduzione posso pensare di stampare una versione del file con le key + ast con i riferimenti
        # poi si può caricare il file tradotto con le key e renderizzare il twee?
        

        sys.exit(0)

    else:
        console.print("[blue]Usage:python main.py «path/to/storyfile.twee»[/]")
        sys.exit(1)


def path_validator(path: str) -> bool:
    # not implement unofficial .twee2 and .tw2
    if os.path.exists(path):
        if path.endswith(".twee") or path.endswith(".tw"):
            return True
    return False

def file_loader(path: str) -> str:
    if not path_validator(path):
        raise Exception(f"invalid path or invalid file")
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    if not raw:
        raise Exception("can't parsing an empty story")
    return raw

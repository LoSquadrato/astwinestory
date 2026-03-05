import sys
import os
from rich.console import Console
from rich.text import Text
from core.parser.parser import Parser
from core.parser.extract_story import extract_story
#from core.validator.path_validator import path_validator, Exception
#from core.parser.extract_story import extract_story

console = Console()

def repl(path):

    console.print("This is StoryLoom!!", style="bold cyan")
    if path_validator(path):
        text = file_loader(path)
        story = extract_story(text)
                           
                    # se non ci sono errori vado con la seconda parte
                    # scelta se tradurre in lingua o cambiare formato
                    # per la traduzione posso pensare di stampare una versione del file con le key + ast con i riferimenti
                    # poi si può caricare il file tradotto con le key e renderizzare il twee?
        #except Exception as e:
            #console.print(f"[red]{e}[/]")
            #sys.exit(3)
                # for testing, delete message in future
        console.print("[green]Validation passed.[/]")
        #console.print(f"[green]Extract {len(story_passage_list)} passages.[/]")
                # aggiungo stampo di Story e conteggio passaggi per test
                # User input per scegliere se fare trasferimento tra formati
                # o traduzione o altre funzioni
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
    try:
        valid_path = path_validator(path)
        with open(valid_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        raise Exception(f"can't read file, {e}")
    if not raw:
        raise Exception("can't parsing an empty story")
    return raw

from core.parser.formats import TweeForma

def input_selection(msg : str) -> str:  
    while True:          
        try:
            pos = int(input(f'{msg}\n'))
        except ValueError:
            print('Sorry wrong digit')
            continue
        if conf_input('Are you sure?\n y/N'):
            break
        else:
            print('Sorry this is not a valid answer')
            continue
    return pos   
            
def conf_input(txt):
    # return True se ok False se no
    while True:
        try:
            conf = str(input(txt))
        except ValueError:
            print('Sorry can\'t understand you')
            continue
        if conf.lower() == 'n':
            return False
        elif conf.lower() == 'y':
            return True
        else:
            print('Sorry this is not a valid answer')
            continue
        
def format_selection():
    for f in TweeFormat:
        print(f"{f.value} = {f.name}\n")
    input = input_selection('Enter the number refered to starting format to parse')
    if input in [f.value for f in TweeFormat]:
        pass
    
    
    import sys
import os
from rich.console import Console
from rich.text import Text

from core.parser.formats import TweeFormat, SUPPORTED_FORMAT_VERSIONS
from .valid_input import input_selection

console = Console()

def repl(path):

    console.print("This is StoryLoom CLI!!!", style="bold cyan")
    console.print(f"{path} is your story?", style="bold red")
    console.print("Please do not edit a story if it is not yours", style="bold red")
    console.print("or if you do not have the full right to it", style="bold red")
    if path_validator(path):
        try:
            text = file_loader(path)
            # estratto il testo viene richiesta la definizione del formato
            # da quello si sceglie il parser
            
                
                
                           
            # se non ci sono errori vado con la seconda parte
            # 
                    
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

########################################################

# repl.py — Logica del loop interattivo StoryLoom CLI
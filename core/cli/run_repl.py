from rich.console import Console
from pathlib import Path
from .menus import select_from_menu, get_format_list, FUNCTIONS
from .converter import convert, ConversionError
from core.parser.content_parser import Parser
from core.formats.format_loader import load_format, FORMATS_DIR

console = Console()

def _suggest_output_path(source: Path, format: str) -> Path:
    return source.with_stem(f"{source.stem}_{format}")

def _confirm_output_path(suggested: Path) -> Path:
    print(f"\n{'─' * 50}")
    print(f"  Output suggerito:")
    print(f"  {suggested}")
    print(f"{'─' * 50}")
    print("  [Invio]  Conferma path suggerito")
    print("  [path]   Digita un path alternativo")
    print(f"{'─' * 50}")

    raw = input("  Path output: ").strip()

    if raw == "":
        return suggested

    custom = Path(raw)
    # Se l'utente digita solo un nome senza directory, usare la stessa cartella del sorgente
    if not custom.is_absolute() and custom.parent == Path("."):
        custom = suggested.parent / custom

    return custom

def _file_loader(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        raw = f.read()
    if not raw:
        raise Exception("can't parsing an empty story")
    return raw  


def run_repl(path: Path) -> None:
    
    console.print("This is StoryLoom CLI!!!", style="bold cyan")
    console.print(f"{path} is your story?", style="bold red")
    console.print("Please do not edit a story if it is not yours", style="bold red")
    console.print("or if you do not have the full right to it", style="bold red")
    

    while True:
        # ── Step 1: selezione formato output ──────────────────────────────────
        fmt_option = select_from_menu(
            "Seleziona formato di output", 
            get_format_list(FORMATS_DIR, format_list=[])
            )

        # ── Step 2: selezione funzione ─────────────────────────────────────────
        fn_option = select_from_menu("Seleziona funzione", FUNCTIONS)

        # ── Step 3: conferma / modifica path output ────────────────────────────
        suggested = _suggest_output_path(path, fmt_option)
        output_path = _confirm_output_path(suggested)

        # ── Step 4: esecuzione ─────────────────────────────────────────────────
        print(f"\n  Elaborazione in corso...")
        
        try:
            text = _file_loader(path)
            format_definition = load_format(fmt_option)
            parser = Parser(format_definition)
            parsed_story = parser.parse_story(Parser.split_passage(text))
            console.print("[green]Validation passed.[/]")
            console.print(f"[blue]Title: {parsed_story.title}[/]")
            console.print(f"[blue]Format: {parsed_story.format}[/]")
            console.print(f"[blue]Passages: {len(parsed_story.passages)}[/]")
            # ho il test e il formato di partenza: 
            # 1. carico la FormatDefinition
            # 2. creo il parser (con format definition)
            # 3. 
            # 
                    
        except Exception as e:
            console.print(f"[red]{e}[/]")
            break
                # for testing, delete message in future
        
        # scelta se tradurre in lingua o cambiare formato
        # per la traduzione posso pensare di stampare una versione del file con le key + ast con i riferimenti
        # poi si può caricare il file tradotto con le key e renderizzare il twee?

      
    
'''           
            convert(
                source_path=path,
                output_path=output_path,
                fmt=fmt_option.key,
                function=fn_option.key,
            )
            print(f"\n  ✓ Completato → {output_path}")
        except ConversionError as e:
            print(f"\n  ✗ Errore durante la conversione:\n  {e}")
        except Exception as e:
            print(f"\n  ✗ Errore inatteso:\n  {e}")

        # ── Step 5: continuare o uscire ────────────────────────────────────────
        print(f"\n{'─' * 50}")
        print("  [Invio]  Nuova operazione sullo stesso file")
        print("  [q]      Esci")
        print(f"{'─' * 50}")
        again = input("  > ").strip().lower()
        if again == "q":
            print("\n  Arrivederci.\n")
            break
'''
# converter.py — Stub di conversione, da collegare al parser StoryLoom

from pathlib import Path


class ConversionError(Exception):
    """Errore durante la conversione."""
    pass


def convert(source_path: Path, output_path: Path, fmt: str, function: str) -> None:
    """
    Esegue la conversione del file sorgente nel formato richiesto.

    Args:
        source_path:  Path del file .twee sorgente (già validato)
        output_path:  Path del file di destinazione
        fmt:          Chiave del formato (es. 'twee2', 'twee3', 'twison')
        function:     Chiave della funzione (es. 'convert')

    Raises:
        ConversionError: se la conversione fallisce
    """

    # ── Validazione sorgente ───────────────────────────────────────────────────
    if not source_path.exists():
        raise ConversionError(f"File sorgente non trovato: {source_path}")

    if source_path.suffix.lower() not in (".twee", ".tw"):
        raise ConversionError(
            f"Formato sorgente non supportato: '{source_path.suffix}' "
            "(atteso .twee o .tw)"
        )

    # ── Dispatch funzione ──────────────────────────────────────────────────────
    if function == "convert":
        _run_convert(source_path, output_path, fmt)
    else:
        raise ConversionError(f"Funzione sconosciuta: '{function}'")


def _run_convert(source_path: Path, output_path: Path, fmt: str) -> None:
    """
    Stub della conversione effettiva.
    Sostituire il corpo con la chiamata reale al parser StoryLoom.
    """

    # TODO: sostituire con import e chiamata reale, es:
    #   from storyloom.parser import parse
    #   from storyloom.exporters import export
    #   ast = parse(source_path)
    #   export(ast, output_path, fmt)

    supported = ("twee2", "twee3", "twison")
    if fmt not in supported:
        raise ConversionError(
            f"Formato '{fmt}' non supportato. Disponibili: {', '.join(supported)}"
        )

    # Stub: copia il file sorgente aggiungendo un header di debug
    content = source_path.read_text(encoding="utf-8")
    stub_header = (
        f":: StoryLoom STUB — formato target: {fmt}\n"
        f":: Sorgente: {source_path}\n"
        f":: Output:   {output_path}\n\n"
    )
    output_path.write_text(stub_header + content, encoding="utf-8")

    print(f"\n  [STUB] Conversione simulata → {fmt}")
    print(f"  Sostituire _run_convert() in converter.py con il parser reale.")
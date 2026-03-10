import sys
from pathlib import Path
from core.cli.run_repl import run_repl


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

    try:
        run_repl(source_path)
    except KeyboardInterrupt:
        print("\n\n  Interrupted by the user.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
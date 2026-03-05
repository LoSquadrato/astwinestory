import sys
from repl import repl

def main():

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if path:
            repl(path)
    else:
        print("Usage: python3 main.py «path/to/storyfile»")
        sys.exit(1)

if __name__ == "__main__":
    main()
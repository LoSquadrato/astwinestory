import argparse

from src.parser import split_passage, Parser
import src.format_definition as fmt
from src.utils import load_story, get_format_list, OUTPUT_DIR, parsed_passages_to_json



def main():
    parser = argparse.ArgumentParser(description="Parse a story document.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    verify_parser = subparsers.add_parser("verify", help="Verify the story file")
    verify_parser.add_argument("format", help="name of the format to verify")
    
    format_parser = subparsers.add_parser("list-formats", help="List available formats")
    
    parse_parser = subparsers.add_parser("parse", help="Parse the story file")
    parse_parser.add_argument("format", help="name of the format to parse")
    parse_parser.add_argument("story", help="path to the story file")
    
    args = parser.parse_args()

    
    match args.command:
        case "verify":
            print(f"Verifying format: {args.format}")
            fmt.load_format(args.format)
            print(f"Format {args.format} verified successfully.")
        
        case "list-formats":
            formats = get_format_list()
            print("Available formats:")
            for i, f in enumerate(formats):
                print(f"{i + 1}. {f}")
        
        case "parse":
            print(f"Parsing story: {args.story[-20:]}")
            print(f"with format: {args.format}")
            format = fmt.load_format(args.format)
            story = load_story(args.story)
            passages = split_passage(story)
            parser = Parser(format, passages)
            parser.parse_story()
            print(f"Story {args.story} parsed successfully with format {args.format}.")
            print(f"Total passages parsed: {len(parser.parsed_passages)}")
            parsed_passages_to_json(parser.parsed_passages, parser.story_title)

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
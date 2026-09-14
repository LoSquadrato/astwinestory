import argparse



def main():
    parser = argparse.ArgumentParser(description="Parse a story document.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    verify_parser = subparsers.add_parser("verify", help="Verify the story file")
    verify_parser.add_argument("format", help="name of the format to verify")
    
    
    args = parser.parse_args()

    
    match args.command:
        case "verify":
            print("Verifying the story file...")
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
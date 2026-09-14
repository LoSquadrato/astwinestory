# handler for the command line interface of the StoryLoom tool

from dataclasses import dataclass
from typing import Callable

from src.render import story_rendering

@dataclass
class HandlerOption():
    key : str
    label : str
    handler : Callable
    extension : str

@dataclass    
class CommandOption():
    format : str
    function : HandlerOption
    output_path : str


HANDLERS_LIST = [
    # HandlerOption(key="convert", label="Convert variables and macros of a story from one format to another", handler=story_rendering, extension=".twee"),
    # HandlerOption(key="extract", label="Extract the text of a story while keeping macro placeholders", handler=text_extractor, extension=".twee"),
    HandlerOption(key="render", label="[only for testing] Render the story text, write a file at output path", handler=story_rendering, extension=".twee"),
]



def handle_command(command: CommandOption, story_content: str) -> None:
    result = {}
    if command.function.key not in [handler.key for handler in HANDLERS_LIST]:
        raise ValueError(f"Unknown command: {command.function.key}")
    match command.function.key:
        case "render":
            result = command.function.handler(story_content, command.output_path)
            with open(command.output_path, "w", encoding="utf-8") as f:
                f.write(result)
            return

def new_command_option(command: dict) -> CommandOption:
    return CommandOption(
        format=command["format"],
        function=command["function"],
        output_path=command["output_path"]
    )
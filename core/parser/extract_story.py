import re
import json
import string
import warnings

from typing import Dict
from core.ast.story import Story
from .formats import TweeFormat
from .errors import ParsingError
from core.validator.storydata_validators import StoryValidator

# extract and validate storydata and storytitle
def extract_story(text: str) -> Story:
    try:
        passages_list = split_passage(text)
        storydata = extract_storydata(passages_list)
    except Exception as e:
        raise ParsingError([str(e)])
    validation = StoryValidator.validate(storydata, passages_list)
    
    if validation.warnings:
        for w in validation.warnings:
            print(f"[WARNING] {w}")

    if not validation.is_valid:
        raise ParsingError(validation.errors)

    title = extract_storytitle(passages_list)

    story = Story(
        title=title,
        ifid=storydata.get("ifid"),
        format=TweeFormat(storydata.get("format")),
        format_version=storydata.get("format-version"),
        start_passage=storydata.get("start"),
    )

    return story

# split file twee in a list of every passage
def split_passage(text: str) -> list[str]:
    if "::" in text and "\n" not in text:
        raise ParsingError([
            "The file contains '::' but no newline characters. "
            "The Twee file may have been flattened into a single line."
        ])
    passage_cut = re.compile(r"(?=^::)", re.MULTILINE)
    passages_list = passage_cut.split(text)
    return passages_list[1:]


def extract_storydata(passages_list: list[str]) -> Dict[str, str]:
    storydata_dict = None
    for passage in passages_list:
        if "StoryData" in passage.strip():
            data = re.findall(r'\{(.*)\}', passage, re.DOTALL)
            if not data:
                warnings.warn("failed to extract StoryData content")
            try:
                storydata_dict = json.loads('{' + data[0] + '}')
            except json.JSONDecodeError as e:
                raise ParsingError([f"failed StoryData verification: {e}"])
    if storydata_dict is None or len(storydata_dict) == 0:
        raise ParsingError([f"missing StoryData content"])
    return storydata_dict
        

def extract_storytitle(passages_list: list[str]) -> str:
    storytitle = None
    for passage in passages_list:
        if "StoryTitle" in passage.strip():
            storytitle = passage.split("StoryTitle", 1)[1]
            break
    return storytitle

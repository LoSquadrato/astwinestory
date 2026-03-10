import re
import json
import string
import warnings

from typing import Dict
from core.ast.story import Story
from .formats import TweeFormat
from .content_parser import ParsingError
from core.parser.formats.sugarcube.storydata_validators import StoryValidator

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

# to do: create func for other special passages: StorySubtitle, StoryAuthor, StoryMenu, StorySettings, StoryIncludes, stylesheet and script, UserStylesheet, UserScript

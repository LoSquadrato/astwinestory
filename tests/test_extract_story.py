import json
import uuid

import pytest

from core.parser.formats.sugarcube.extract_story import (
    split_passage,
    extract_storydata,
    extract_storytitle,
    extract_story,
)
from core.parser.errors import ParsingError
from core.ast.story import Story


# helpers ---------------------------------------------------------------------

def make_basic_twee(ifid: str = None, fmt: str = "SugarCube", version: str = "2.37.3", start: str = "Start") -> str:
    if ifid is None:
        ifid = str(uuid.uuid4())
    return f"""
:: StoryTitle
My title

:: StoryData
{{
    "ifid": "{ifid}",
    "format": "{fmt}",
    "format-version": "{version}",
    "start": "{start}"
}}

:: {start}
The first passage.
""".strip()


# tests -----------------------------------------------------------------------

def test_split_passage_happy_path():
    text = ":: A\ncontent\n:: B\nmore"
    parts = split_passage(text)
    assert len(parts) == 2
    assert parts[0].startswith(":: A")
    assert parts[1].startswith(":: B")


def test_split_passage_flattened_raises():
    text = "::A::B"
    with pytest.raises(ParsingError):
        split_passage(text)


def test_extract_storydata_and_title():
    twee = make_basic_twee()
    passages = split_passage(twee)
    storydata = extract_storydata(passages)
    title = extract_storytitle(passages)

    assert storydata["format"] == "SugarCube"
    assert title.strip() == "My title"


def test_extract_story_happy_path():
    twee = make_basic_twee()
    story = extract_story(twee)

    assert isinstance(story, Story)
    assert story.title.strip() == "My title"
    assert story.format.value == "SugarCube"


def test_extract_story_missing_storydata():
    text = ":: StoryTitle\nfoo"
    with pytest.raises(ParsingError):
        extract_story(text)


def test_extract_story_invalid_json():
    twee = """
:: StoryTitle
Title

:: StoryData
{ not json }
"""
    with pytest.raises(ParsingError):
        extract_story(twee)

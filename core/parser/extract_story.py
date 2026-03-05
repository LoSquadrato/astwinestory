import re
import json
import string
import warnings

from typing import Dict
from core.ast.story import Story
from formats import TweeFormat
from errors import ParsingError



def extract_story(text : str) -> Story:
    passage_list = split_passage(text)
    try:
        storydata = extract_storydata(passage_list)
        title = extract_storytitle(passage_list)
    except Exception as e:
        print("Error")
    try:
        story = Story(
            title=title,
            ifid=storydata.get("ifid"),
            format=TweeFormat(storydata.get("format")),
            format_version=storydata.get("format-version"),
            start_passage=storydata.get("start"),
        )
    except ParsingError as e:
        print(e)
    return story

def split_passage(text: str) -> list[str]:
    passage_list = text.split("::")
    if len(passage_list) < 2:
        raise Exception("too less of passages find, need almost StoryTitle and StoryData")
    return passage_list

 
def extract_storydata(passage_list: list[str]) -> Dict[str, str]:
    storydata_dict = None
    for passage in passage_list:
        if passage.strip().startswith("StoryData"):
            data = str(re.findall(r'(?<=\{)(?:[^{}]|\{[^{}]*\})*(?=\})', passage))
            if not data:
                raise warnings.warn("failed to extract StoryData content")
            try:
                storydata_dict = json.loads((data[0]))
            except json.JSONDecodeError as e:
                raise Exception(f"failed StoryData verification: {e}") 
    if storydata_dict == None or len(storydata_dict) == 0:
        raise Exception(f"missing StoryData content")   
    return storydata_dict
        

def extract_storytitle(passage_list: list[str]) -> str:
    storytitle = None
    for passage in passage_list:
        passage = passage.strip()
        if passage.startswith("StoryTitle"):
            storytitle = passage.split("StoryTitle", 1)[1]
            break
    return storytitle

'''
# check key lowercase, need to change other check func like this
def check_start(storydata_dict: dict[str,str]) -> str:
    start = None
    for k, v in storydata_dict:
        if k.lower() == "start":
            start = v
    if start is None or len(start) == 0:
        raise Exception(f"empty or None start content")
    return start


def check_ifid(storydata_dict: dict[str,str]) -> str:
    if storydata_dict.get("ifid") is None:
        raise Exception("empty or None ifid content")
    ifid = str(storydata_dict["ifid"])
    if len(ifid) != 36:
        raise Exception(f"IFID code has to be long at least 36 char")
    return ifid


def check_format(storydata_dict: dict[str,str]) -> str:
    if storydata_dict.get("format") is None:
        raise Exception("None format content")
    format_str = str(storydata_dict["format"])
    if len(format_str) == 0:
        raise Exception(f"empty format content")
    try:
        format = TweeFormat(format_str)
    except Exception:
        raise Exception(f"unsupported format '{format_str}'. Supported: {[f.value for f in TweeFormat]}")
    return format.value


def check_format_version(storydata_dict: dict[str,str]) -> str:
    if storydata_dict.get("format-version") is None:
        raise Exception("None format-version content")
    format_version = str(storydata_dict["format-version"])
    if len(format_version) == 0:
        raise Exception(f"Empty format-version content")
    return format_version

'''
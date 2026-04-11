import pytest
from core.parser.content_render import Render, RenderingError
from core.parser import Parser
from core.formats import load_format

def test_render():
    story = '''
    :: StoryTitle
    This is the story title.
    
    :: Macros
    <<set $name to "World">>
    
    :: link
    [[Go to passage|Passage1]]
    
    :: variable
    $name
    
    :: operator, formatting and literal
    a + b = null 
    ''formatting''
    
    :: Meta
    [metanode]
    '''
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    parsed_story = parser.parse_story(Parser.split_passage(story))
    renderer = Render(parsed_story)
    rendered_story = renderer.render_story(parsed_story)
    assert "This is the story title." in rendered_story
    assert "<<set $name to \"World\">>" in rendered_story
    assert "[[Go to passage|Passage1]]" in rendered_story
    assert "$name" in rendered_story
    assert "a + b = null" in rendered_story
    assert "''formatting''" in rendered_story
    assert "[metanode]" in rendered_story
from core.src import story_rendering
from core.src.parser import Parser
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
    
    :: HTML
    <div class="my-class">Hello, World!</div>
    
    :: Meta
    [metanode]
    '''
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    parsed_story, _ = parser.parse_story(Parser.split_passage(story))
    rendered_story = story_rendering(parsed_story)
    assert "This is the story title." in rendered_story
    assert "<<set $name to \"World\">>" in rendered_story
    assert "[[Go to passage|Passage1]]" in rendered_story
    assert "$name" in rendered_story
    assert "a + b = null" in rendered_story
    assert "''formatting''" in rendered_story
    assert "<div class=\"my-class\">Hello, World!</div>" in rendered_story
    assert "[metanode]" in rendered_story
    

def test_render_variable():
    story = '''
    :: StoryTitle
    This is a $variable.
    
    '''
    fmt = load_format("SugarCube")
    parser = Parser(fmt)
    parsed_story, _ = parser.parse_story(Parser.split_passage(story))
    rendered_story = story_rendering(parsed_story)
    assert "This is a $variable." in rendered_story
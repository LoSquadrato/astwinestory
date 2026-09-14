import pytest
from cli.run_repl import _validate_output_path, file_loader
from core.config import MAX_STORY_SIZE

def test_validare_output_path(tmp_path):
    # create a temp directory to simulate the source
    source = tmp_path / "source"
    source.mkdir()
    # create a file with the same name to test renaming
    (source / "testfile.txt").write_text("dummy content")
    # call the function
    result_path = _validate_output_path(source, "testfile", ".txt")
    # check that the returned path has the "_1" suffix
    assert result_path.endswith("testfile_1.txt")
    
        
def test_file_loader(tmp_path):
    # create a temp file with some content
    valid_file = tmp_path / "valid_story.twee"
    valid_file.write_text("This is a valid story.")
    
    # test loading a valid file
    content = file_loader(valid_file)
    assert content == "This is a valid story."
    
    # test loading a non-existent file
    non_existent_file = tmp_path / "nonexistent.twee"
    with pytest.raises(FileNotFoundError):
        file_loader(non_existent_file)
    
    # test loading an empty file
    empty_file = tmp_path / "empty_story.twee"
    empty_file.write_text("")
    with pytest.raises(ValueError):
        file_loader(empty_file)
    
    # test loading a file that exceeds the max size
    large_file = tmp_path / "large_story.twee"
    large_file.write_text("A" * (MAX_STORY_SIZE + 1))  # exceed max size
    with pytest.raises(ValueError):
        file_loader(large_file)
    

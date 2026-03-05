import os
import sys
import tempfile
import unittest


from core.validator.path_validator import (
    path_validator,
    file_loader,
    check_storytitle,
    check_start,
    check_ifid,
    check_format,
    check_format_version,
    ValidationError,
)


class TestValidator(unittest.TestCase):
    # path_validator
    def test_path_validator_accepts_twee(self):
        # create a temporary file with .twee extension
        with tempfile.NamedTemporaryFile(suffix=".twee", delete=False) as tmp:
            tmp.write(b"Hello")
            tmp_path = tmp.name
        try:
            result = path_validator(tmp_path)
            self.assertEqual(result, tmp_path)
        finally:
            os.remove(tmp_path)

    def test_path_validator_rejects_wrong_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with self.assertRaises(Exception) as cm:
                path_validator(tmp_path)
            self.assertIn("please select .twee or .tw file", str(cm.exception))
        finally:
            os.remove(tmp_path)

    def test_path_validator_nonexistent_raises(self):
        with self.assertRaises(Exception):
            path_validator("/non/existent/path.twee")

    # file_loader
    def test_file_loader_reads_content(self):
        with tempfile.NamedTemporaryFile(suffix=".twee", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write("some content")
            tmp_path = tmp.name
        try:
            content = file_loader(tmp_path)
            self.assertEqual(content, "some content")
        finally:
            os.remove(tmp_path)

    def test_file_loader_empty_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".twee", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with self.assertRaises(ValidationError):
                file_loader(tmp_path)
        finally:
            os.remove(tmp_path)

    def test_file_loader_invalid_path_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            file_loader("nope.twee")

    # check_storytitle
    def test_check_storytitle_success(self):
        # typical passage list element returned by parser may already strip leading markers
        passages = ["StoryTitle MyStory", ":: StoryData"]
        title = check_storytitle(passages)
        self.assertEqual(title, "MyStory")

    def test_check_storytitle_missing(self):
        passages = [":: SomethingElse"]
        with self.assertRaises(Exception):
            check_storytitle(passages)

    # check_start
    def test_check_start_success(self):
        meta = {"start": "Beginning"}
        self.assertEqual(check_start(meta), "Beginning")

    def test_check_start_missing_raises(self):
        with self.assertRaises(ValidationError):
            check_start({})

    def test_check_start_empty_raises(self):
        with self.assertRaises(ValidationError):
            check_start({"start": ""})

    # check_ifid
    def test_check_ifid_success(self):
        meta = {"ifid": "a" * 36}
        self.assertEqual(check_ifid(meta), "a" * 36)

    def test_check_ifid_missing_raises(self):
        with self.assertRaises(ValidationError):
            check_ifid({})

    def test_check_ifid_wrong_length(self):
        with self.assertRaises(ValidationError):
            check_ifid({"ifid": "short"})

    # check_format
    def test_check_format_success(self):
        meta = {"format": "SugarCube"}
        self.assertEqual(check_format(meta), "SugarCube")

    def test_check_format_missing(self):
        with self.assertRaises(ValidationError):
            check_format({})

    def test_check_format_empty(self):
        with self.assertRaises(ValidationError):
            check_format({"format": ""})

    def test_check_format_unsupported(self):
        with self.assertRaises(ValidationError) as cm:
            check_format({"format": "Unknown"})
        self.assertIn("unsupported format", str(cm.exception))

    # check_format_version
    def test_check_format_version_success(self):
        meta = {"format-version": "2.0"}
        self.assertEqual(check_format_version(meta), "2.0")

    def test_check_format_version_missing(self):
        with self.assertRaises(ValidationError):
            check_format_version({})

    def test_check_format_version_empty(self):
        with self.assertRaises(ValidationError):
            check_format_version({"format-version": ""})


if __name__ == "__main__":
    unittest.main()

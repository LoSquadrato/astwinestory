import uuid

import pytest

from core.validator.storydata_validators import StoryValidator, ValidationResult
from core.parser.formats import SUPPORTED_FORMAT_VERSIONS


VALID_IFID = str(uuid.uuid4())


def test_validate_structure_missing_fields():
    result = StoryValidator.validate({}, [])
    assert "Missing IFID" in result.errors
    assert "Missing start node" in result.errors
    assert "Missing format" in result.errors
    assert not result.is_valid


def test_validate_semantics_invalid_ifid():
    data = {"ifid": "not-a-uuid", "format": "SugarCube", "format-version": "2.0"}
    result = StoryValidator.validate(data, [])
    assert any("Invalid IFID" in e for e in result.errors)


def test_validate_semantics_unsupported_format():
    data = {"ifid": VALID_IFID, "format": "UnknownFormat", "format-version": "1.0"}
    result = StoryValidator.validate(data, [])
    assert any("Unsupported format" in e for e in result.errors)


def test_validate_semantics_version_warning():
    # choose a supported format but a version not in list to trigger warning
    fmt = list(SUPPORTED_FORMAT_VERSIONS.keys())[0]
    data = {
        "ifid": VALID_IFID,
        "format": fmt,
        "format-version": "deadbeef",
        "start": "foo",
    }
    result = StoryValidator.validate(data, [])
    assert result.is_valid
    assert result.warnings, "expected a version warning"


def test_validate_success():
    fmt = list(SUPPORTED_FORMAT_VERSIONS.keys())[0]
    version = SUPPORTED_FORMAT_VERSIONS[fmt][0]
    data = {"ifid": VALID_IFID, "format": fmt, "format-version": version, "start": "foo"}
    result = StoryValidator.validate(data, [])
    assert result.is_valid
    assert not result.errors
    assert not result.warnings

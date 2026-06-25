"""Unit tests for app.services.document_parser."""
import pytest

from app.core.exceptions import InvalidFileError, TextExtractionError
from app.services.document_parser import clean_text, extract_text, get_extension


def test_get_extension_returns_lowercase_extension():
    assert get_extension("Resume.PDF") == "pdf"
    assert get_extension("resume.docx") == "docx"


def test_get_extension_rejects_unsupported_type():
    with pytest.raises(InvalidFileError):
        get_extension("resume.exe")


def test_get_extension_rejects_no_extension():
    with pytest.raises(InvalidFileError):
        get_extension("resume")


def test_extract_text_from_txt_bytes():
    raw = b"Experienced Python developer.\n\nSkills: Flask, Docker."
    text = extract_text(raw, "resume.txt")
    assert "Experienced Python developer" in text
    assert "Flask" in text


def test_extract_text_empty_txt_raises():
    with pytest.raises(TextExtractionError):
        extract_text(b"   \n\n   ", "resume.txt")


def test_clean_text_collapses_excess_whitespace():
    raw = "Hello    world\n\n\n\nGoodbye"
    cleaned = clean_text(raw)
    assert "    " not in cleaned
    assert "\n\n\n" not in cleaned


def test_clean_text_strips_null_bytes():
    raw = "Hello\x00World"
    cleaned = clean_text(raw)
    assert "\x00" not in cleaned

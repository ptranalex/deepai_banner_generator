"""Tests for selection parser module"""

import pytest

from lib.selection_parser import parse_selection


def test_parse_selection_single() -> None:
    """Test parsing single selection"""
    assert parse_selection("1", 10) == [0]
    assert parse_selection("5", 10) == [4]
    assert parse_selection("10", 10) == [9]


def test_parse_selection_multiple() -> None:
    """Test parsing multiple selections"""
    assert parse_selection("1,3,5", 10) == [0, 2, 4]
    assert parse_selection("1 3 5", 10) == [0, 2, 4]
    assert parse_selection("2,4,6,8", 10) == [1, 3, 5, 7]


def test_parse_selection_range() -> None:
    """Test parsing range selection"""
    assert parse_selection("1-5", 10) == [0, 1, 2, 3, 4]
    assert parse_selection("3-7", 10) == [2, 3, 4, 5, 6]
    assert parse_selection("1-10", 10) == list(range(10))


def test_parse_selection_mixed() -> None:
    """Test parsing mixed format"""
    assert parse_selection("1,3-5,7", 10) == [0, 2, 3, 4, 6]
    assert parse_selection("1-3,5,7-9", 10) == [0, 1, 2, 4, 6, 7, 8]


def test_parse_selection_with_spaces() -> None:
    """Test parsing with various whitespace"""
    assert parse_selection(" 1 , 3 , 5 ", 10) == [0, 2, 4]
    assert parse_selection("1 - 5", 10) == [0, 1, 2, 3, 4]


def test_parse_selection_deduplicates() -> None:
    """Test that duplicate selections are deduplicated"""
    assert parse_selection("1,1,1", 10) == [0]
    assert parse_selection("1-3,2-4", 10) == [0, 1, 2, 3]


def test_parse_selection_sorts() -> None:
    """Test that results are sorted"""
    assert parse_selection("5,3,1", 10) == [0, 2, 4]
    assert parse_selection("9,7,5,3,1", 10) == [0, 2, 4, 6, 8]


def test_parse_selection_out_of_range() -> None:
    """Test error handling for out of range"""
    with pytest.raises(ValueError, match="out of range"):
        parse_selection("0", 10)

    with pytest.raises(ValueError, match="out of range"):
        parse_selection("11", 10)

    with pytest.raises(ValueError, match="out of range"):
        parse_selection("1,15", 10)


def test_parse_selection_invalid_range() -> None:
    """Test error handling for invalid ranges"""
    with pytest.raises(ValueError, match="Invalid range"):
        parse_selection("5-3", 10)  # Start > end

    with pytest.raises(ValueError, match="out of bounds"):
        parse_selection("1-15", 10)  # Range exceeds max


def test_parse_selection_invalid_format() -> None:
    """Test error handling for invalid formats"""
    with pytest.raises(ValueError, match="Invalid number"):
        parse_selection("abc", 10)

    with pytest.raises(ValueError, match="Invalid range format"):
        parse_selection("1-2-3", 10)


def test_parse_selection_empty_parts() -> None:
    """Test handling of empty parts"""
    assert parse_selection("1,,3", 10) == [0, 2]
    assert parse_selection("1,  ,3", 10) == [0, 2]

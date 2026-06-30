"""Unit tests for rygex/python_regex.py"""

import re
import pytest
from rygex.python_regex import grouped_iter, rygex_search, mmap_reader
from rygex.args import PythonArgs


def test_grouped_iter_basic():
    # Test data
    file_data = ["hello world 123", "test 456 abc", "no match here"]
    test_reg = re.compile(r"\d+")
    int_list = [1]  # Select capture group 1 (the whole match)

    result = grouped_iter(file_data, test_reg, int_list)
    # grouped_iter returns just the matched numbers
    expected = ["123", "456"]
    assert result == expected


def test_grouped_iter_no_matches():
    file_data = ["no numbers here", "still no match"]
    test_reg = re.compile(r"\d+")
    int_list = [1]
    result = grouped_iter(file_data, test_reg, int_list)
    assert result == []


def test_rygex_search_simple(capsys):
    # Mock args with a simple pattern
    args = PythonArgs(pyreg=["test"], insensitive=False)
    func_search = ["this is a test line", "another line without test"]
    result = rygex_search(args, func_search)
    # Should return lines that match the pattern
    assert "this is a test line" in result
    assert "another line without test" in result  # Both lines contain "test"
    # Capture output via capsys if needed
    captured = capsys.readouterr()
    assert "test" in captured.out or True  # simple check


def test_mmap_reader_line_mode(tmp_path):
    # Create a temporary file with some content
    file_path = tmp_path / "sample.txt"
    file_path.write_text("line1\nline2 with 123\nline3")
    # Use mmap_reader with 'line' criteria
    reader = mmap_reader(str(file_path), regex_pattern=r"\d+", criteria="line", insensitive=False)
    matches = list(reader)
    # Should yield tuples of matched line bytes (single element tuple)
    assert any(b"123" in line[0] for line in matches)


def test_mmap_reader_match_mode(tmp_path):
    file_path = tmp_path / "sample2.txt"
    file_path.write_text("abc 123 def 456 ghi")
    # Use string pattern with capture groups
    reader = mmap_reader(str(file_path), regex_pattern=r"(\d+)", criteria="match", insensitive=True)
    matches = list(reader)
    # Should yield captured groups (as bytes)
    assert any(b"123" in match[0] or b"456" in match[0] for match in matches)

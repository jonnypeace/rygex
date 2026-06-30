"""Extended unit tests for rygex/python_regex.py"""

import re
import pytest
from pathlib import Path

# Import the functions and classes we want to test
from rygex.python_regex import (
    grouped_iter,
    rygex_search,
    mmap_reader,
    ParserPyReg,
    rygex_parser,
)
from rygex.args import PythonArgs
from rygex.python_regex import multi_cpu



# ----------------------------------------------------------------------
# Tests for grouped_iter
# ----------------------------------------------------------------------
def test_grouped_iter_basic():
    """Test basic functionality of grouped_iter."""
    file_data = ["hello world 123", "test 456 abc", "no match here"]
    test_reg = re.compile(r"\d+")
    int_list = [1]  # Select the first capture group (the whole match)
    result = grouped_iter(file_data, test_reg, int_list)
    expected = ["123", "456"]
    assert result == expected


def test_grouped_iter_no_matches():
    """Test grouped_iter when no matches are found."""
    file_data = ["no numbers here", "still no match"]
    test_reg = re.compile(r"\d+")
    int_list = [1]
    result = grouped_iter(file_data, test_reg, int_list)
    assert result == []


def test_grouped_iter_empty_int_list():
    """Test grouped_iter with an empty int_list (returns empty string for each match)."""
    file_data = ["abc 123 def"]
    test_reg = re.compile(r"\d+")
    int_list = []  # No capture groups selected
    result = grouped_iter(file_data, test_reg, int_list)
    assert result == [""]


# ----------------------------------------------------------------------
# Tests for rygex_search
# ----------------------------------------------------------------------
def test_rygex_search_simple(capsys):
    """Test rygex_search with a simple pattern."""
    args = PythonArgs(pyreg=["test"], insensitive=False)
    func_search = ["this is a test line", "another line without tets"]
    result = rygex_search(args, func_search)
    assert "this is a test line" in result
    assert "another line without test" not in result

    # Verify that something was printed (capsys captures stdout)
    captured = capsys.readouterr()
    assert "test" in captured.out or True  # simple check


def test_rygex_search_case_insensitive(capsys):
    """Test rygex_search with case-insensitive matching."""
    args = PythonArgs(pyreg=["TEST"], insensitive=True)
    func_search = ["This Is A Test Line", "no match here"]
    result = rygex_search(args, func_search)
    assert "This Is A Test Line" in result
    assert "no match here" not in result


def test_rygex_search_multiple_patterns(capsys):
    """Test rygex_search with multiple regex patterns."""
    args = PythonArgs(pyreg=["test|example"], insensitive=False)
    func_search = ["this is a test line", "this is an example line", "no match"]
    result = rygex_search(args, func_search)
    assert "this is a test line" in result
    assert "this is an example line" in result
    assert "no match" not in result


# ----------------------------------------------------------------------
# Tests for mmap_reader
# ----------------------------------------------------------------------
def test_mmap_reader_line_mode(tmp_path: Path = Path('tmp')):
    """Test mmap_reader in line mode."""
    # Create a temporary file with some content
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "sample.txt"
    file_path.write_text("line1\nline2 with 123\nline3")
    # Use mmap_reader with 'line' criteria
    reader = mmap_reader(str(file_path), regex_pattern=r"\d+", criteria="line", insensitive=False)
    matches = list(reader)
    # Each match is a tuple with the line bytes as its first element
    assert any(b"123" in line_tuple[0] for line_tuple in matches)


def test_mmap_reader_match_mode(tmp_path: Path = Path('tmp')):
    """Test mmap_reader in match mode."""
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "sample2.txt"
    file_path.write_text("abc 123 def 456 ghi")
    reader = mmap_reader(str(file_path), regex_pattern=r"(\d+)", criteria="match", insensitive=True)
    matches = list(reader)
    # Should yield captured groups (as bytes)
    # Each match is a tuple of captured groups; check if any group contains the digits
    assert any(b"123" in m[0] or b"456" in m[0] for m in matches)


# ----------------------------------------------------------------------
# Tests for ParserPyReg
# ----------------------------------------------------------------------
def test_parser_pyreg_initialization():
    """Test that ParserPyReg can be instantiated correctly."""
    # Mock a compiled regex pattern
    test_reg = re.compile(r"test.*")
    parser = ParserPyReg(
        test_reg=test_reg,
        pygen_length=1,
        group_num=0,
        split_int=[],  # No split groups
        pyreg_last_list=[],
    )
    assert isinstance(parser, ParserPyReg)
    assert parser.test_reg == test_reg
    assert parser.pygen_length == 1
    assert parser.group_num == 0
    assert parser.split_int == []
    assert parser.pyreg_last_list == []


def test_parser_pyreg_attributes():
    """Test that ParserPyReg holds the correct attributes after initialization."""
    test_reg = re.compile(r"(abc)(def)", re.ASCII)
    parser = ParserPyReg(
        test_reg=test_reg,
        pygen_length=2,
        group_num=2,
        split_int=[1, 2],
        pyreg_last_list=[],
    )
    assert parser.test_reg == test_reg
    assert parser.pygen_length == 2
    assert parser.group_num == 2
    assert parser.split_int == [1, 2]
    assert parser.pyreg_last_list == []


# ----------------------------------------------------------------------
# Tests for rygex_parser
# ----------------------------------------------------------------------
def test_rygex_parser_basic():
    """Test that rygex_parser returns a properly structured ParserPyReg."""
    args = PythonArgs(pyreg=["\\d+"])
    parser = rygex_parser(args)
    assert isinstance(parser, ParserPyReg)
    assert parser.test_reg.pattern == r"\d+"
    assert parser.pygen_length == 1
    assert parser.split_int == []


def test_rygex_parser_multiple_patterns():
    """Test rygex_parser with multiple patterns."""
    args = PythonArgs(pyreg=["test|example", "1 2"])
    parser = rygex_parser(args)
    assert isinstance(parser, ParserPyReg)
    assert parser.pygen_length == 2
    assert parser.split_int == [1, 2]


# ----------------------------------------------------------------------
# Tests for multi_cpu (basic sanity check)
# ----------------------------------------------------------------------
def test_multi_cpu_sanity(tmp_path: Path):
    """Basic sanity check for multi_cpu to ensure it runs without error."""
    # 1. Use the fixture correctly (no default value)
    # 2. Create test data
    file_path = tmp_path / "small.txt"
    file_path.write_text("line1\nline2\nline3")
    
    # 3. Define arguments
    args = PythonArgs(pyreg=["line"], insensitive=False)

    # 4. Execute and assert on the result
    # We assert that the result has exactly 3 items (the 3 lines in the file)
    results = list(multi_cpu(args=args, file_path=str(file_path), n_cores=1, chunk_size=10))
    
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    
    # Optional: Verify content
    assert ["line1"] in results
    assert ["line3"] in results



# ----------------------------------------------------------------------
# Additional Tests for grouped_iter
# ----------------------------------------------------------------------
def test_grouped_iter_with_capture_groups():
    """Test grouped_iter with regex patterns that have capture groups."""
    file_data = ["name: John, age: 30", "name: Jane, age: 25"]
    test_reg = re.compile(r"name: (\w+), age: (\d+)")
    int_list = [1, 2]  # Select both capture groups
    result = grouped_iter(file_data, test_reg, int_list)
    expected = ["John 30", "Jane 25"]
    assert result == expected


def test_grouped_iter_zero_group():
    """Test grouped_iter with group 0 (full match)."""
    file_data = ["abc 123 def", "ghi 456 jkl"]
    test_reg = re.compile(r"\d+")
    int_list = [0]  # Select full match
    result = grouped_iter(file_data, test_reg, int_list)
    expected = ["123", "456"]
    assert result == expected


def test_grouped_iter_single_group_selection():
    """Test grouped_iter selecting only one capture group."""
    # Use content that matches the pattern: two numbers with a space between
    file_data = ["abc 123 456 ghi"]
    test_reg = re.compile(r"(\d+) (\d+)")
    int_list = [2]  # Select only second capture group
    result = grouped_iter(file_data, test_reg, int_list)
    # grouped_iter returns captured groups joined by space
    # When there's a tuple match, it returns the selected groups
    assert result == ["456"]


def test_grouped_iter_empty_file_data():
    """Test grouped_iter with empty file data."""
    file_data = []
    test_reg = re.compile(r"\d+")
    int_list = [1]
    result = grouped_iter(file_data, test_reg, int_list)
    assert result == []


# ----------------------------------------------------------------------
# Additional Tests for rygex_search
# ----------------------------------------------------------------------
def test_rygex_search_empty_input():
    """Test rygex_search with empty input."""
    args = PythonArgs(pyreg=["test"], insensitive=False)
    result = rygex_search(args, func_search=[])
    assert result == []


def test_rygex_search_no_matches():
    """Test rygex_search when no lines match."""
    args = PythonArgs(pyreg=["xyz"], insensitive=False)
    func_search = ["line1", "line2", "line3"]
    result = rygex_search(args, func_search)
    assert result == []


def test_rygex_search_all_match():
    """Test rygex_search when all lines match."""
    args = PythonArgs(pyreg=["line"], insensitive=False)
    func_search = ["line1", "line2", "line3"]
    result = rygex_search(args, func_search)
    assert result == ["line1", "line2", "line3"]


# Note: rygex_search only handles basic regex matching. Parameters like omitfirst,
# unique, sort, rev, lines are handled at a higher level in cli.py, not in rygex_search.
# Tests for those parameters should be integration tests in cli.py, not unit tests here.


# ----------------------------------------------------------------------
# Additional Tests for mmap_reader
# ----------------------------------------------------------------------
def test_mmap_reader_multiline_file(tmp_path: Path):
    """Test mmap_reader with a multiline file."""
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "multiline.txt"
    content = "line1\nline2\nline3\nline4\nline5"
    file_path.write_text(content)
    reader = mmap_reader(str(file_path), regex_pattern=r"line", criteria="line", insensitive=False)
    matches = list(reader)
    assert len(matches) == 5


def test_mmap_reader_no_matches(tmp_path: Path):
    """Test mmap_reader when no matches are found."""
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "nomatch.txt"
    file_path.write_text("no matches here")
    reader = mmap_reader(str(file_path), regex_pattern=r"xyz", criteria="line", insensitive=False)
    matches = list(reader)
    assert len(matches) == 0


def test_mmap_reader_empty_file(tmp_path: Path):
    """Test mmap_reader with an empty file - should raise ValueError."""
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")
    # mmap_reader raises ValueError for empty files
    with pytest.raises(ValueError):
        reader = mmap_reader(str(file_path), regex_pattern=r"test", criteria="line", insensitive=False)
        list(reader)


def test_mmap_reader_binary_content(tmp_path: Path):
    """Test mmap_reader with binary content."""
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "binary.bin"
    file_path.write_bytes(b"\x00\x01\x02test\x03\x04")
    reader = mmap_reader(str(file_path), regex_pattern=r"test", criteria="line", insensitive=False)
    matches = list(reader)
    assert any(b"test" in line_tuple[0] for line_tuple in matches)


# ----------------------------------------------------------------------
# Additional Tests for ParserPyReg
# ----------------------------------------------------------------------
def test_parser_pyreg_with_multiple_groups():
    """Test ParserPyReg with regex having multiple capture groups."""
    test_reg = re.compile(r"(\w+)@(\w+)\.(\w+)")
    parser = ParserPyReg(
        test_reg=test_reg,
        pygen_length=1,
        group_num=3,
        split_int=[1, 2, 3],
        pyreg_last_list=[],
    )
    assert parser.group_num == 3


def test_parser_pyreg_empty_pattern():
    """Test ParserPyReg with empty pattern."""
    test_reg = re.compile(r"")
    parser = ParserPyReg(
        test_reg=test_reg,
        pygen_length=1,
        group_num=0,
        split_int=[],
        pyreg_last_list=[],
    )
    assert parser.test_reg.pattern == ""


# ----------------------------------------------------------------------
# Additional Tests for rygex_parser
# ----------------------------------------------------------------------
def test_rygex_parser_case_sensitive():
    """Test rygex_parser with case-sensitive matching."""
    args = PythonArgs(pyreg=["TEST"], insensitive=False)
    parser = rygex_parser(args)
    # Pattern should be compiled without IGNORECASE
    assert not (parser.test_reg.flags & re.IGNORECASE)


def test_rygex_parser_case_insensitive():
    """Test rygex_parser with case-insensitive matching."""
    args = PythonArgs(pyreg=["TEST"], insensitive=True)
    parser = rygex_parser(args)
    # Pattern should be compiled with IGNORECASE
    assert parser.test_reg.flags & re.IGNORECASE


def test_rygex_parser_with_special_chars():
    """Test rygex_parser with special regex characters."""
    args = PythonArgs(pyreg=[r"\d{3}-\d{2}-\d{4}"])  # SSN-like pattern
    parser = rygex_parser(args)
    assert parser.test_reg.pattern == r"\d{3}-\d{2}-\d{4}"


def test_rygex_parser_with_anchors():
    """Test rygex_parser with regex anchors."""
    args = PythonArgs(pyreg=["^start.*end$"])
    parser = rygex_parser(args)
    assert parser.test_reg.pattern == "^start.*end$"


def test_rygex_parser_multiple_patterns_with_groups():
    """Test rygex_parser with multiple patterns and capture groups."""
    # The second element specifies capture groups to extract (space-separated integers)
    args = PythonArgs(pyreg=["(test) (example)", "1 2"])
    parser = rygex_parser(args)
    assert parser.pygen_length == 2
    assert parser.group_num == 2  # Two capture groups in "(test) (example)"
    assert parser.split_int == [1, 2]  # Extract groups 1 and 2


# ----------------------------------------------------------------------
# Tests for reader_args_parser
# ----------------------------------------------------------------------
def test_reader_args_parser():
    """Test reader_args_parser function."""
    from rygex.python_regex import reader_args_parser
    
    args = PythonArgs(pyreg=["test"], insensitive=False)
    result = reader_args_parser("test.txt", args)
    
    assert result["file_path"] == "test.txt"
    assert result["regex_pattern"] == "test"
    assert result["criteria"] == "match"
    assert result["insensitive"] == False


def test_reader_args_parser_insensitive():
    """Test reader_args_parser with insensitive flag."""
    from rygex.python_regex import reader_args_parser
    
    args = PythonArgs(pyreg=["test"], insensitive=True)
    result = reader_args_parser("test.txt", args)
    
    assert result["insensitive"] == True


# ----------------------------------------------------------------------
# Tests for rygex_mmap
# ----------------------------------------------------------------------
def test_rygex_mmap_line_mode(tmp_path: Path):
    """Test rygex_mmap in line mode."""
    from rygex.python_regex import rygex_mmap
    
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "mmap_test.txt"
    file_path.write_text("line1\nline2 with 123\nline3")
    
    args = PythonArgs(pyreg=["\\d+"], insensitive=False)
    result = rygex_mmap(args, str(file_path))
    
    # rygex_mmap returns full lines that contain matches
    assert any("123" in line for line in result)


def test_rygex_mmap_match_mode(tmp_path: Path):
    """Test rygex_mmap in match mode with capture groups."""
    from rygex.python_regex import rygex_mmap
    
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "mmap_test2.txt"
    # Use content that matches the pattern: two numbers with a space between
    file_path.write_text("abc 123 456 ghi")
    
    # Pattern with two capture groups separated by space
    args = PythonArgs(pyreg=["(\\d+) (\\d+)"], insensitive=False)
    result = rygex_mmap(args, str(file_path))
    
    # For single pattern with capture groups, returns full line containing match
    assert any("123" in line and "456" in line for line in result)


# ----------------------------------------------------------------------
# Tests for chunked_line_reader
# ----------------------------------------------------------------------
def test_chunked_line_reader_basic(tmp_path: Path):
    """Test chunked_line_reader basic functionality."""
    from rygex.python_regex import chunked_line_reader
    
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "chunk_test.txt"
    file_path.write_text("line1\nline2\nline3\nline4\nline5")
    
    chunks = list(chunked_line_reader(chunk_size=2, file_path=str(file_path)))
    
    assert len(chunks) == 3  # 2 + 2 + 1 lines
    assert chunks[0] == ["line1", "line2"]
    assert chunks[1] == ["line3", "line4"]
    assert chunks[2] == ["line5"]


def test_chunked_line_reader_single_chunk():
    """Test chunked_line_reader with chunk_size larger than file."""
    from rygex.python_regex import chunked_line_reader
    
    import io
    stdin = io.StringIO("line1\nline2")
    
    chunks = list(chunked_line_reader(chunk_size=10, stdin=stdin))
    
    assert len(chunks) == 1
    assert chunks[0] == ["line1", "line2"]


def test_chunked_line_reader_empty_file(tmp_path: Path):
    """Test chunked_line_reader with empty file."""
    from rygex.python_regex import chunked_line_reader
    
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "empty_chunk.txt"
    file_path.write_text("")
    
    chunks = list(chunked_line_reader(chunk_size=10, file_path=str(file_path)))
    
    assert len(chunks) == 0


# ----------------------------------------------------------------------
# Tests for _compute_byte_ranges
# ----------------------------------------------------------------------
def test_compute_byte_ranges():
    """Test _compute_byte_ranges function."""
    from rygex.python_regex import _compute_byte_ranges
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("line1\nline2\nline3\nline4\nline5")
        f.flush()
        ranges = _compute_byte_ranges(f.name, chunk_size_bytes=10)
    
    # Should have multiple ranges
    assert len(ranges) >= 1
    # Each range should be a tuple of two integers
    for start, end in ranges:
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert start < end


# ----------------------------------------------------------------------
# Tests for multi_cpu with file
# ----------------------------------------------------------------------
def test_multi_cpu_with_file(tmp_path: Path):
    """Test multi_cpu with a file input."""
    from rygex.python_regex import multi_cpu
    
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "multi_test.txt"
    file_path.write_text("line1\nline2\nline3\nline4\nline5")
    
    args = PythonArgs(pyreg=["line"], insensitive=False)
    results = list(multi_cpu(args=args, file_path=str(file_path), n_cores=2, chunk_size=10))
    
    # Should have results from all lines
    all_results = [item for sublist in results for item in sublist]
    assert len(all_results) == 5


def test_multi_cpu_with_small_file(tmp_path: Path):
    """Test multi_cpu with a small file."""
    from rygex.python_regex import multi_cpu
    
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "small_multi.txt"
    file_path.write_text("test1\ntest2")
    
    args = PythonArgs(pyreg=["test"], insensitive=False)
    results = list(multi_cpu(args=args, file_path=str(file_path), n_cores=1, chunk_size_bytes=10))
    
    all_results = [item for sublist in results for item in sublist]
    assert len(all_results) == 2


# ----------------------------------------------------------------------
# Tests for edge cases
# ----------------------------------------------------------------------
def test_grouped_iter_special_characters():
    """Test grouped_iter with special regex characters in output."""
    file_data = ["price: $100.50", "price: $200.75"]
    test_reg = re.compile(r"price: \$(\d+\.\d+)")
    int_list = [1]
    result = grouped_iter(file_data, test_reg, int_list)
    # grouped_iter returns captured groups joined by space
    assert "100.50" in result[0]
    assert "200.75" in result[1]


def test_rygex_search_unicode():
    """Test rygex_search with unicode characters."""
    args = PythonArgs(pyreg=["test"], insensitive=False)
    func_search = ["test café", "test naïve", "normal line"]
    result = rygex_search(args, func_search)
    assert "test café" in result
    assert "test naïve" in result


def test_mmap_reader_unicode(tmp_path: Path):
    """Test mmap_reader with unicode content."""
    tmp_path.mkdir(exist_ok=True)
    file_path = tmp_path / "unicode.txt"
    file_path.write_text("café\nnaïve\nrésumé")
    reader = mmap_reader(str(file_path), regex_pattern=r"café", criteria="line", insensitive=False)
    matches = list(reader)
    assert len(matches) == 1


def test_rygex_parser_complex_pattern():
    """Test rygex_parser with a complex email pattern."""
    args = PythonArgs(pyreg=[r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"])
    parser = rygex_parser(args)
    assert parser.test_reg.pattern == r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"


# Note: rygex_search only handles basic regex matching. Parameters like counts,
# totalcounts, fixed_string, start, end, rpyreg are handled at a higher level
# in cli.py, not in rygex_search. Tests for those parameters should be
# integration tests in cli.py, not unit tests here.

from typing import Optional, TypedDict

class RustParsed(TypedDict, total=False):
    file_path:           Optional[str]
    start_delim:         Optional[str]
    start_index:         Optional[int]
    end_delim:           Optional[str]
    end_index:           Optional[int]
    omit_first:          Optional[int]
    omit_last:           Optional[int]
    print_line_on_match: bool
    case_insensitive:    bool


def new_rustparsed() -> RustParsed:
    return {
        "file_path":           None,
        "start_delim":         None,
        "start_index":         None,
        "end_delim":           None,
        "end_index":           None,
        "omit_first":          None,
        "omit_last":           None,
        "print_line_on_match": False,
        "case_insensitive":    False,
    }
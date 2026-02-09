import argparse
# import importlib.metadata
# from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional, Union, NamedTuple
from .version import __version__

# __version__ = importlib.metadata.version("rygex")


# @dataclass
class PythonArgs(NamedTuple):
    start:        Optional[list[str]]         = None
    end:          Optional[list[str]]         = None
    fixed_string: Optional[str]               = None
    file:         Optional[Path]              = None
    insensitive:  bool                        = False
    omitfirst:    Optional[int]               = None
    omitlast:     Optional[int]               = None
    omitall:      bool                        = False
    pyreg:        Optional[list[str]]         = None
    rpyreg:       Optional[list[str]]         = None
    lines:        Optional[Union[int, slice]] = None
    sort:         bool                        = False
    rev:          bool                        = False
    unique:       bool                        = False
    counts:       bool                        = False
    totalcounts:  bool                        = False
    multi:        Optional[int]               = None
    gen:          Optional[list[str]]         = None
    # Note: we do NOT store “version” here, because we're using argparse’s built-in
    #       action="version" (which never puts a “version” attribute in the Namespace).


def parse_slice(s: str) -> Union[int, slice]:
    """
    Turn:
      '5'     → 5
      '2:10'  → slice(2,10)
      '3:15:2'→ slice(3,15,2)
      ':5'    → slice(None,5)
      '-1'    → -1
    """
    if ":" in s:
        parts = s.split(":")
        if len(parts) not in (2, 3):
            raise argparse.ArgumentTypeError(f"Invalid slice syntax: {s!r}")
        start = int(parts[0]) if parts[0] else None
        stop  = int(parts[1]) if parts[1] else None
        step  = int(parts[2]) if (len(parts) == 3 and parts[2]) else None
        return slice(start, stop, step)
    try:
        return int(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer index: {s!r}")


class NoEllipsisFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        # For -s/--start, -e/--end, -p/--pyreg, -rp/--rpyreg: force "PATTERN [INDEX]"
        if action.dest in ("start", "end", "pyreg", "rpyreg"):
            opts = ", ".join(action.option_strings)
            return f"{opts} PATTERN [INDEX]"
        return super()._format_action_invocation(action)



def get_args() -> PythonArgs:
    """
    Parse command-line args and always return a PythonArgs. If `-v/--version`
    is passed, argparse will do its own print+exit, so we never “fall off the end.”
    """
    pk = argparse.ArgumentParser(
        prog="rygex",
        description="Search files with keywords, characters or python regex",
        formatter_class=NoEllipsisFormatter,
    )

    pk.add_argument(
        "-s", "--start",
        metavar=("TEXT", "INDEX"),
        help=(
            "Starting string search:  -s PATTERN [INDEX]  "
            "(requires --end)."
        ),
        type=str,
        nargs="+",
        required=False,
    )

    pk.add_argument(
        "-e", "--end",
        metavar=("TEXT", "INDEX"),
        help=(
            "End of string search:  -e PATTERN [INDEX]  "
            "(requires --start)."
        ),
        type=str,
        nargs="+",
        required=False,
    )

    pk.add_argument(
        "-F", "--fixed-string",
        metavar="TEXT",
        help="Search and print lines containing exactly TEXT",
        type=str,
        required=False,
        default=None,
    )

    pk.add_argument(
        "-f", "--file",
        metavar="PATH/FILENAME",
        help="Filename to search through",
        type=Path,
        required=False,
    )

    pk.add_argument(
        "-i", "--insensitive",
        help="Case-insensitive matching",
        action="store_true",
        required=False,
    )

    pk.add_argument(
        "-of", "--omitfirst",
        metavar="INDEX",
        help="Remove INDEX chars from left side of --start match",
        type=int,
        required=False,
        default=None,
    )

    pk.add_argument(
        "-ol", "--omitlast",
        metavar="INDEX",
        help="Remove INDEX chars from right side of --end match",
        type=int,
        required=False,
        default=None,
    )

    pk.add_argument(
        "-O", "--omitall",
        help="Remove chars from both --start and --end matches",
        action="store_true",
        required=False,
    )

    pk.add_argument(
        "-p", "--pyreg",
        metavar=("PATTERN", "INDEX"),
        help="Python regex: PATTERN [INDEX]",
        type=str,
        nargs="+",
        required=False,
    )

    pk.add_argument(
        "-rp", "--rpyreg",
        metavar=("PATTERN", "INDEX"),
        help="Reversed Python regex: PATTERN [INDEX]",
        type=str,
        nargs="+",
        required=False,
    )

    pk.add_argument(
        "-l", "--lines",
        metavar="SLICE",
        help=(
            "Slice in the form start:stop[:step], e.g. ':10' for first 10, "
            "'-1' for last entry, or '-5:' for last 5."
        ),
        type=parse_slice,
        required=False,
        default=None,
    )

    pk.add_argument(
        "-S", "--sort",
        help="Sort the output (combine with --rev for reverse)",
        action="store_true",
        required=False,
    )

    pk.add_argument(
        "-r", "--rev",
        help="Reverse the sort order",
        action="store_true",
        required=False,
    )

    pk.add_argument(
        "-u", "--unique",
        help="Only show unique matches",
        action="store_true",
        required=False,
    )

    pk.add_argument(
        "-c", "--counts",
        help="Show match counts",
        action="store_true",
        required=False,
    )

    pk.add_argument(
        "-t", "--totalcounts",
        help="Show total count of matches",
        action="store_true",
        required=False,
    )

    pk.add_argument(
        "-m", "--multi",
        metavar="CORES",
        nargs="?",
        type=int,
        const=(os.cpu_count() or 1),
        default=None,
        help=(
            "Number of CPU cores to use; if you pass `-m` with no value, "
            "it picks all available cores. If you omit it, no multiprocessing."
        ),
    )

    pk.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program’s version number and exit",
    )

    pk.add_argument(
        "-g", "--gen",
        metavar=("PATTERN", "INDEX"),
        help="Generator-based Python regex: PATTERN [INDEX] (optional)",
        type=str,
        nargs="+",
        required=False,
    )

    args = pk.parse_args()

    return PythonArgs(**vars(args))

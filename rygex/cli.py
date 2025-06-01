#!/usr/bin/env python3

r"""
rygex - Python string and regex search
=======================================

SYNOPSIS
========
./rygex.py [-s keyword/character [position]] | [-p regex [position|all]] [-e keyword/character position] [-i] [-l int|$|$-int|int-int] [-of] [-ol] [-f /path/to/file]

Author and Github
=================
Author: Jonny Peace, email: jonnypeace@outlook.com
Link for further information can be found here...
https://github.com/jonnypeace/rygex/blob/main/README.md

Description
===========
Python string and regex search made easy. Select characters/keywords from and to sections of a line, further enhance with python regex, and specific lines.
Can accept stdin from a pipe or using the -f|--file flag

OPTIONS
=======
-s  | --start       can be used standlone (without --pyreg) or with --pyreg. [keyword/character [position]]
-e  | --end         is optional. Provides an end to the line you are searching for. [keyword/character position]
-of | --omitfirst   is optional for deleting the first characters of your match. Only works with --start
-ol | --omitlast    is optional and same as --omitfirst. Only works with --end
-l  | --lines       is optional and to save piping using tail, head or sed. [int|$|$-int|int-int|int-$]
-p  | --pyreg       can be used standlone (without --start) or with --start. [regex [position|all]]
-i  | --insensitive When used, case insensitive search is used. No args required.
-O  | --omitall     Optional, combination of -ol and -of
-u  | --unique      Optional, filters out lines which are the same, no further args necessary
-S  | --sort        Optional, currently sorts, but no reverse option supported yet, no further args necessary.
-c  | --counts      Optional, counts the number of lines which are the same, no further args necessary. Created unique output.
-f  | --file        /path/to/file.

Examples
========
 -s can be run with position being equal to all, to capture the start of the line
 ./rygex.py -s root all -f /etc/passwd                 ## output: root:x:0:0::/root:/bin/bash
 ./rygex.py -s root 1 -e \: 4 -f /etc/passwd           ## output: root:x:0:0:
 ./rygex.py -s CRON 1 -e \) 2 -f /var/log/syslog       ## Output: CRON[108490]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
 ./rygex.py -s jonny 2 -f /etc/passwd                  ## output: jonny:/bin/bash

 without -of -ol -O
 ./rygex.py -s \( 1 -e \) 1 -f testfile                ## output: (2nd line, 1st bracket)
 with -of -ol
 ./rygex.py -s \( 1 -e \) 1 -of -ol -f testfile        ## output:  2nd line, 1st bracket

-p or --pyreg | I recommend consulting the python documentation for python regex using re.
 with -s & -p

 ./rygex.py -s Feb -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test

 with -p
./rygex.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test
"""

import argparse, re, sys, os, gc, mmap, math
from pathlib import Path
from typing import Iterable, Generator, Literal, TypedDict, NamedTuple
from dataclasses import dataclass
import rygex_ext as regex
from collections.abc import Sequence
import importlib.metadata 
from collections import Counter

from functools import partial
from itertools import islice
from typing import List, Tuple, Any, Callable


# (1) Define your package version in one place, e.g. in pyproject.toml / setup.cfg
#     so importlib.metadata.version() can pick it up.
__version__ = importlib.metadata.version("rygex")


def print_err(msg):
    '''
    Print error messages, to std error and exit with exit code 1.
    '''
    colours = {'fail': '\033[91m', 'end': '\033[0m'}
    print(f'{colours["fail"]}{msg}{colours["end"]}', file=sys.stderr)
    exit(1)

# sense checking commandline input.
def sense_check(args,
                argTty: bool=False):
    '''
    Check args are sufficient for processing.
    '''

    # if not stdin or file, error
    if not args.file and argTty:
        print_err('Requires stdin from somewhere, either from --file or pipe')

    # Removed the required field for start, with the intention to use either start or pyreg, and build a pyreg function
    if not args.start and not args.pyreg and not args.rpyreg and not args.fixed_string and not args.gen:
        print_err('This programme requires the (--start --end) or -p or -rp or - F flag to pattern match properly')

    if args.pyreg and len(args.pyreg) > 2:
        print_err('--pyreg can only have 2 args... search pattern and option')

    if args.start and len(args.start) > 2:
        print_err('--start has too many arguments, character or word followed by occurent number')

    if not args.start and args.pyreg and (args.omitall or args.omitfirst or args.omitlast):
        print_err('error, --pyreg not supported with --omitfirst or --omitlast or --omitall')

    if args.omitfirst and args.start == None:
        print_err('error, --omitfirst without --start')

    if args.omitlast and args.end == None:
        print_err('error, --omitlast without --end')

    if (args.omitall and args.omitfirst) or (args.omitall and args.omitlast):
        print_err('error, --omitfirst or --omitlast cant be used with --omitall')
    
    if args.start:
        if not len(args.start) > 1 and ( args.omitall or args.omitfirst or args.omitlast):
            print_err('error, --start requires numerical index with --omitfirst or --omitlast or --omitall')
        if not args.end:
            print_err('error, --start requires --end ')

    if args.file and not args.file.is_file():
        print_err(f'error, --file {args.file} does not exist')

def lower_search(file_list: Generator,
                 args,
                 checkFirst: int=0,
                 checkLast: int=0)-> list:
    '''Lower start seach is case insensitive'''
    # If positional number value not set, default to all.
    if len(args.start) < 2:
        args.start.append('all')
    try:
        if len(args.end) < 2:
            args.end.append('all')
    except TypeError:
        pass # args.end is not mandatory, returns None when not called, so just pass.
    # If arg.start[1] does not equal 'all'...
    # Change arg.start[1] to int, since it will be a string.
    if args.start[1] != 'all':
        try:
            iter_start = int(args.start[1])
        except ValueError:
            print_err('Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args')

    # Sense check args.end and ensure 2nd arg is an int
    if args.end and args.end[1] != 'all':
        try:
            iter_end = int(args.end[1])
            if args.start[0] == args.end[0]:
                iter_end += 1
        except ValueError:
            print_err('ValueError: -e / --end only accepts number values')
    start_end: list= []
    # variables from the optional argument of excluding one character
    for line in file_list:
        lower_line = line.casefold()
        lower_str = args.start[0].casefold()
        if args.end:
            lower_end = args.end[0].casefold()
        if lower_str in lower_line:
            try:
                new_str = line
                # Start Arg position and initial string creation.
                if args.start[1] != 'all':
                    init_start = lower_line.index(lower_str)
                    new_str = line[init_start:]
                    new_index = new_str.casefold().index(lower_str)
                    for _ in range(iter_start -1):
                        new_index = new_str.casefold().index(lower_str, new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if args.end and args.end[1] != 'all':
                    new_index = new_str.casefold().index(lower_end)
                    length_end = len(args.end[0])
                    for _ in range(iter_end -1):
                        new_index = new_str.casefold().index(lower_end, new_index + 1)
                    new_str = new_str[:new_index + length_end]
                start_end.append(new_str[checkFirst:checkLast])
                # ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                # ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                # so we would want to pass those as well.
            except ValueError:
                pass
    return start_end

def normal_search(file_list: Generator,
                  args,
                  checkFirst: int=0,
                  checkLast: int=0)-> list:
    '''Normal start search, case sensitive'''
    # If positional number value not set, default to all.
    if len(args.start) < 2:
        args.start.append('all')
    try:
        if len(args.end) < 2:
            args.end.append('all')
    except TypeError:
        pass # args.end is not mandatory, returns None when not called, so just pass.
    # If arg.start[1] does not equal 'all'...
    # Change arg.start[1] to int, since it will be a string.
    if args.start[1] != 'all':
        try:
            iter_start = int(args.start[1])
        except ValueError:
            print_err('Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args')

    # Sense check args.end and ensure 2nd arg is an int
    if args.end and args.end[1] != 'all':
        try:
            iter_end = int(args.end[1])
            if args.start[0] == args.end[0]:
                iter_end += 1
        except ValueError:
            print_err('ValueError: -e / --end only accepts number values or "all"')
    start_end: list= []
    # variables from the optional argument of excluding one character
    for line in file_list:
        if args.start[0] in line:
            try:
                new_str = line
                # Start Arg position and initial string creation.
                if args.start[1] != 'all':
                    init_start = line.index(args.start[0])
                    new_str = line[init_start:]
                    new_index = new_str.index(args.start[0])
                    for _ in range(iter_start -1):
                        new_index = new_str.index(args.start[0], new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if args.end and args.end[1] != 'all':
                    new_index = new_str.index(args.end[0])
                    length_end = len(args.end[0])
                    for _ in range(iter_end -1):
                        new_index = new_str.index(args.end[0], new_index + 1)
                    new_str = new_str[:new_index + length_end]
                start_end.append(new_str[checkFirst:checkLast])
                # ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                # ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                # so we would want to pass those as well.
            except ValueError:
                pass
    return start_end

def grouped_iter(file_data: Iterable[str],test_reg: re.Pattern, int_list=None):
    temp_list: list = []
    for line in file_data:
        reg_match = test_reg.findall(line)
        if reg_match:
            all_group = ''
            if int_list:
                for i in int_list:
                    all_group = all_group + ' ' + reg_match[0][i-1]
            else:
                for i in reg_match[0]:
                    all_group = all_group + ' ' + i
            temp_list.append(all_group[1:])
    return temp_list

def rygex_search(args=None, func_search: Iterable[str] = None,
                  pos_val: int=0)-> list:
    '''Python regex search using --pyreg, can be either case sensitive or insensitive'''
    parsed = rygex_parser(args)
    
    if parsed.pygen_length == 1: # defaults to printing full line if regular expression matches
        for line in func_search:
            reg_match = parsed.test_reg.findall(line)
            if reg_match:
                parsed.pyreg_last_list.append(line)

    elif parsed.pygen_length == 2:
        if args.pyreg[1] == '0':
            if parsed.group_num > 1:
                parsed.pyreg_last_list = grouped_iter(file_data=func_search, test_reg=parsed.test_reg)
            if parsed.group_num == 1:
                for line in func_search:
                    reg_match = parsed.test_reg.findall(line)
                    if reg_match:
                        parsed.pyreg_last_list.append(reg_match[0])
        elif len(parsed.split_str) == 1:
            try:
                pos_val = int(parsed.split_str[0])
            except ValueError: #valueError due to pos_val being a string
                print_err(f'only string allowed to be used with pyreg is "all", check args {parsed.split_str}')
            for line in func_search:
                reg_match = parsed.test_reg.findall(line)
                if reg_match:
                    try:
                        parsed.pyreg_last_list.append(reg_match[0][pos_val - 1]) if parsed.group_num > 1 else parsed.pyreg_last_list.append(reg_match[pos_val - 1])
                    #indexerror when list exceeds index available
                    except (IndexError):
                        print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')
        elif len(parsed.split_str) > 1:
            try:
                # Create an int list for regex match iteration.
                int_list: list[int] = [int(i) for i in parsed.split_str]
            except ValueError: # Value error when incorrect values for args.
                print_err(f'Error. Index chosen {parsed.split_str} are incorrect. Options are "all" or number value, i.e. "1 2 3" ')
            try:
                parsed.pyreg_last_list = grouped_iter(func_search,parsed.test_reg, int_list)
            except IndexError:
                print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')

    return parsed.pyreg_last_list


def omit_check(first=None, last=None, args=None)-> tuple:
    '''Omit characters for --start and --end args'''
    if args.omitall:
        try:
            first = len(args.start[0])
            last = - len(args.end[0])
        except TypeError:
            print_err('--start and --end required for omitall, and will automatically reduce by length of word')
        return first, last

    if args.omitfirst and isinstance(args.omitfirst[0], int):
        first = int(args.omitfirst[0])

    if args.omitlast and isinstance(args.omitlast[0], int):
        last = - int(args.omitlast[0])
    return first, last
        

def format_counts(counts: Sequence[tuple[str,int]], args) -> list[str]:
    """
    Given a list of (key, count) tuples from Rust, apply your
    --sort/--rev/--lines logic and return lines like:
      "{key:<{padding}}Line-Counts = {count}"
    """
    # Determine padding
    padding = max(len(k) for k, _ in counts) + 4

    # Start with Rust’s sorted list
    items = list(counts)

    # Python-side sort flag (if you still want Python sort)
    if args.sort:
        items.sort(key=lambda kv: kv[1], reverse=True)

    # Reverse if requested
    if args.rev:
        items = list(reversed(items))

    # Apply --lines filtering if requested
    if args.lines != slice(None, None, None):
        items = items[args.lines[0]]

    # Format
    return [f"{k:{padding}}Line-Counts = {v}" for k, v in items]


def parse_slice(s: str):
    """
    Turn
      '5'     → 5            (an int index)
      '2:10'  → slice(2,10)
      '3:15:2'→ slice(3,15,2)
      ':5'    → slice(None,5)
      '-1'    → -1           (last element)
    """
    if ':' in s:
        parts = s.split(':')
        if len(parts) not in (2,3):
            raise argparse.ArgumentTypeError(f"Invalid slice syntax: {s!r}")
        start = int(parts[0]) if parts[0] else None
        stop  = int(parts[1]) if parts[1] else None
        step  = int(parts[2]) if len(parts)==3 and parts[2] else None
        return slice(start, stop, step)
    # no colon → must be an integer
    try:
        return int(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer index: {s!r}")


class NoEllipsisFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        # when we’re printing the "-s/--start" bit:
        if action.dest in ("start", 'end', 'pyreg', 'rpyreg'):
            opts = ", ".join(action.option_strings)
            # force it to look like exactly one PATTERN plus an optional INDEX
            return f"{opts} PATTERN [INDEX]"
        # otherwise, fall back to argparse’s normal behavior
        return super()._format_action_invocation(action)


def get_args():
    '''Setting arg parser args'''
    pk = argparse.ArgumentParser(
        prog='rygex',
        description='Search files with keywords, characters or python regex',
        formatter_class=NoEllipsisFormatter
        )

    pk.add_argument('-s', '--start',
        metavar=('TEXT', 'INDEX'),
        help='This is the starting string search -s text_pattern optional[index] Note: Requires --end',
        type=str,
        required=False,
        nargs='+',
        )

    pk.add_argument('-e', '--end',
        metavar=('TEXT', 'INDEX'),
        help='end of string search -e text_pattern optional[index] Note: Requires --start',
        type=str,
        nargs='+',
        required=False)
    
    pk.add_argument('-F', '--fixed-string',
        help='Search and print lines with fixed string -F text_pattern',
        type=str,
        required=False,
        default=None,
        nargs=1,
        metavar='TEXT', 
        )

    pk.add_argument('-f', '--file',
        help='filename to string search through',
        type=Path,
        metavar='PATH/FILENAME', 
        required=False)

    pk.add_argument('-i', '--insensitive',
        help='This is just a flag for case insensitive for the start flag, no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument('-of', '--omitfirst',
        help='optional argument for --start. -of [int] - Removes characters from --start (left) side of ouput',
        type=int,
        nargs=1,
        default=None,
        metavar='[INDEX]', 
        required=False)

    pk.add_argument('-ol', '--omitlast',
        help='optional argument for --end. -ol [int] - Removes characters from --end (right) side of ouput',
        type=int,
        nargs=1,
        default=None,
        metavar='[INDEX]',
        required=False)
    
    pk.add_argument('-O', '--omitall',
        help='optional argument for --start & --end. -O [int] - Removes characters from --start & --end of ouput',
        action='store_true',
        required=False)

    pk.add_argument('-p', '--pyreg',
        help='python regular expression, use with -p "pattern" and follow up with a numerical value for a capture group (optional)',
        type=str,
        metavar=('PATTERN', 'INDEX'),
        nargs='+',
        required=False)
    
    pk.add_argument('-rp', '--rpyreg',
        metavar=('PATTERN', 'INDEX'),
        help='python regular expression, use with -rp "pattern" and follow up with a numerical value for a capture group (optional)',
        type=str,
        nargs='+',
        required=False)

    pk.add_argument('-l', '--lines',
        help='slice in the form start:stop[:step], e.g. :10 first 10 entries or -1 for last entry or -5: for last 5',
        type=parse_slice,
        nargs=1,
        default=slice(None, None, None),
        metavar='SLICE', 
        required=False)

    pk.add_argument('-S', '--sort',
        help='Can be used standalone for normal sort, or combined with --rev for reverse',
        action='store_true',
        required=False)
    
    pk.add_argument('-r', '--rev',
        help='Can be used standalone or with --sort',
        action='store_true',
        required=False)
    
    pk.add_argument('-u', '--unique',
        help='This is just a flag for unique matches no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument('-c', '--counts',
        help='This is just a flag for counting matches no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument('-t', '--totalcounts',
        help='This is just a flag for counting total matches no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument(
        '-m', '--multi',
        metavar='CORES',
        nargs='?',
        type=int,
        const=(os.cpu_count() or 1),
        default=None,
        help=(
            "number of CPU cores to use;\n"
            "if you omit the value (just '-m'), it picks all available cores;\n"
            "if you omit the flag entirely, it won't do multiprocessing"
        ))
    
    pk.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="show program’s version number and exit"
    )
    
    pk.add_argument(
        '-g', '--gen',
        metavar=('PATTERN', 'INDEX'),
        help='python regular expression, use with -g "pattern" and follow up with a numerical value for a capture group (optional) Uses Generators',
        type=str,
        nargs='+',
        required=False
    )
    args = pk.parse_args()

    return args

class PythonArgs:
    '''
    Class purely for parsing using python and portability.
    '''
    
    def __init__(self, **kwargs) -> None:

        self.start: str | list = kwargs.get('start')
        self.end: str | list = kwargs.get('end')
        self.insensitive: bool = kwargs.get('insensitive', False)

        # Omitfirst and Omitlast need list conditions for compatibility with the commandline syntax.
        # And I would rather not pass a omitfirst=list[int] for PythonArgs
        # And I would rather not enclose the False syntax in a list.
        # The reason for bool, is to make sure comparisons are made in sense check, instead of a list of None.
        self.omitfirst: list[int] | bool = [ kwargs.get('omitfirst', False) ] if kwargs.get('omitfirst', False) != False else False
        self.omitlast: list[int] | bool = [ kwargs.get('omitlast', False) ] if kwargs.get('omitlast', False) != False else False
        
        self.omitall: bool = kwargs.get('omitall', False)
        self.lines: list[str] =  [ kwargs.get('lines') ]
        self.sort: bool = kwargs.get('sort', False)
        self.rev: bool = kwargs.get('rev', False)
        self.unique: bool = kwargs.get('unique', False)
        self.counts: bool = kwargs.get('counts', False)
        self.pyreg: str | list = kwargs.get('pyreg')
        self.file: Path = Path(kwargs.get('file')) # type: ignore
        self.multi: int = kwargs.get('multi' )


# def chunked_file_reader(chunk_size: int, file_path: str = None, stdin: sys.stdin = None) -> Iterable[list[str]]: # multi threaded
#     '''Yields chunks of lines from a file or stdin'''
#     chunk = []
#     try:
#         source = open(file_path, 'r') if file_path else stdin
#         if not source:
#             print_err('Input Error: Either file_path or stdin must be provided')
#         for line in source:
#             chunk.append(line.strip())
#             if len(chunk) >= chunk_size:
#                 yield chunk
#                 chunk = []
#         if chunk:
#             yield chunk
#     finally:
#         if file_path:
#             source.close()


def mmap_reader(file_path: str, regex_pattern: str, criteria: Literal['line', 'match'], insensitive: bool = False): # single threaded

    with open(file_path, 'rb', buffering=0) as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # Compile the regular expression pattern
            pattern = re.compile(regex_pattern.encode('utf-8'), re.IGNORECASE) if insensitive else re.compile(regex_pattern.encode('utf-8'))
            # Search using the pattern, yielding match objects
            match criteria:
                case 'line':
                    for match in pattern.finditer(mm):
                        start = max(0, mm.rfind(b'\n', 0, match.start())+1)
                        end = mm.find(b'\n', match.end())
                        if end == -1:
                            end = len(mm)  # Handle case where the match is in the last line
                        # Append the whole line as a decoded string
                        yield mm[start:end].decode('utf-8')
                case 'match':
                    for match in pattern.finditer(mm):
                        yield match.groups()
                
                case _:
                    print_err('Internal error with criteria matching')

@dataclass
class ParserPyReg:
    test_reg: re.Pattern
    pygen_length: int
    group_num: int
    split_str: list
    pyreg_last_list: list

def rygex_parser(args):

    test_reg: re.Pattern = re.compile(args.pyreg[0], re.IGNORECASE) if args.insensitive else re.compile(args.pyreg[0])
    # Splitting the arg for capture groups into a list
    try:
        split_str: list = args.pyreg[1].split(' ')
    # IndexError occurs when entire lines are required
    except IndexError:
        split_str = []

    return ParserPyReg(
        test_reg = test_reg,
        split_str = split_str,
        pygen_length = len(args.pyreg),
        group_num = test_reg.groups,
        pyreg_last_list = []
    )

class ReaderArgs(TypedDict):
    file_path: str
    regex_pattern: str
    criteria: Literal['line', 'match']
    insensitive: bool = False

def reader_args_parser(file_path, args):
    return ReaderArgs(
        file_path=file_path,
        regex_pattern=args.pyreg[0],
        criteria='match',
        insensitive=args.insensitive
    )


def rygex_mmap(args, file_path, pos_val): # single threaded
    '''Python regex search using --pyreg, can be either case sensitive or insensitive'''
    parsed = rygex_parser(args)
    reader_args: ReaderArgs = reader_args_parser(file_path, args)

    match parsed.pygen_length:
        case 1: # defaults to printing full line if regular expression matches
            reader_args['criteria'] = 'line'
            for line in mmap_reader(**reader_args):
                parsed.pyreg_last_list.append(line)
        case 2:
            if args.pyreg[1] == 'all':
                if parsed.group_num > 1:
                    for line in mmap_reader(**reader_args):
                        all_group: str = ''
                        for i in line:
                            all_group = all_group + ' ' + i.decode()
                        parsed.pyreg_last_list.append(all_group[1:])
                if parsed.group_num == 1:
                    for line in mmap_reader(**reader_args):
                        parsed.pyreg_last_list.append(line[0].decode())
            elif len(parsed.split_str) == 1:
                try:
                    pos_val = int(parsed.split_str[0])
                except ValueError: #valueError due to pos_val being a string
                    print_err(f'only string allowed to be used with pyreg is "all", check args {parsed.split_str}')
                for line in mmap_reader(**reader_args):
                    try:
                        parsed.pyreg_last_list.append(line[pos_val-1].decode())
                    #indexerror when list exceeds index available
                    except (IndexError):
                        print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')
            elif len(parsed.split_str) > 1:
                try:
                    # Create an int list for regex match iteration.
                    int_list: list[int] = [int(i) for i in parsed.split_str]
                except ValueError: # Value error when incorrect values for args.
                    print_err(f'Error. Index chosen {parsed.split_str} are incorrect. Options are "all" or number value, i.e. "1 2 3" ')
                for line in mmap_reader(**reader_args):
                    all_group = ''
                    try:
                        for i in int_list:
                            all_group = all_group + ' ' + line[i - 1].decode()
                        parsed.pyreg_last_list.append(all_group[1:])
                    # Indexerror due to incorrect index
                    except IndexError:
                        print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')

    return parsed.pyreg_last_list


###########################

def unified_input_reader(file_path: str = None) -> Iterable[str]:
    '''Reads lines from a file or stdin'''
    if file_path:
        with open(file_path, 'r') as file:
            for line in file:
                yield line.strip()
    else:
        if not sys.stdin.isatty():
            for line in sys.stdin:
                yield line.strip()

            



# def multi_cpu(pos_val, args, n_cores=2, file_path: str = None)-> Iterable:
#     '''
#     Accepts file_path, pos_val, args, and n_cores (default is system max cores)
#     Only supported with python regex, where multiprocessing above 15 seconds in duration will see a benefit.
#     '''

#     from concurrent.futures import ProcessPoolExecutor
#     global worker
#     def worker(line_list):
#         return rygex_search(args=args, func_search=line_list, pos_val=pos_val)

#     # chunk_size = n_cores * 1000
#     chunk_size = 10000
#     reader_args: dict = {
#         'chunk_size': chunk_size,
#         'file_path': file_path if file_path and Path(file_path).exists() else None,
#         'stdin': sys.stdin if not sys.stdin.isatty() else None
#         }
    
#     with ProcessPoolExecutor(max_workers=n_cores) as executor:
#         result = executor.map(worker, chunked_file_reader(**reader_args))
#         gc.collect()  # Explicitly trigger garbage collection to manage memory

#     for sublist in result:
#         for r in sublist:
#             yield r




# ——— Globals for worker processes ——————————————
_mm: mmap.mmap

def _init_worker(mmap_path: str):
    """Worker initializer: open & mmap the file once, disable GC."""
    global _mm
    f = open(mmap_path, 'rb')
    _mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    gc.disable()

def _rygex_worker_lines(pos_val: Any, args: Any, lines: List[str]) -> List[Any]:
    return rygex_search(args=args, func_search=lines, pos_val=pos_val)

def _rygex_worker_range(pos_val: Any, args: Any, byte_range: Tuple[int,int]) -> List[Any]:
    start, end = byte_range
    chunk = _mm[start:end]
    lines = [ln.decode('utf8', 'ignore') for ln in chunk.splitlines()]
    return rygex_search(args=args, func_search=lines, pos_val=pos_val)

def _compute_byte_ranges(file_path: str, chunk_size_bytes: int) -> List[Tuple[int,int]]:
    """Split the file into newline‐aligned byte ranges ~chunk_size_bytes."""
    size = os.path.getsize(file_path)
    ranges: List[Tuple[int,int]] = []
    with open(file_path, 'rb') as f, \
         mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        offset = 0
        while offset < size:
            end = min(offset + chunk_size_bytes, size)
            mm.seek(end)
            mm.readline()        # advance to end of line
            end = mm.tell()
            ranges.append((offset, end))
            offset = end
    return ranges

# ——— Pure line‐based chunk reader (fallback) ——————
def chunked_line_reader(
    chunk_size: int,
    file_path: str | None = None,
    stdin=None
) -> Iterable[List[str]]:
    """Yield lists of lines (decoded) from file_path or stdin."""
    source = open(file_path, 'r') if file_path else stdin
    if source is None:
        raise ValueError("Need a valid file_path or piped stdin")
    try:
        buf: List[str] = []
        for line in source:
            buf.append(line.rstrip('\n'))
            if len(buf) >= chunk_size:
                yield buf
                buf = []
        if buf:
            yield buf
    finally:
        if file_path:
            source.close()

# ——— multi_cpu that picks the right reader/worker ————
def multi_cpu(
    pos_val: Any,
    args: Any,
    n_cores: int | None = 8,
    file_path: str | None = None,
    # for line‐reader
    chunk_size: int = 10_000,
    # for mmap reader
    chunk_size_bytes: int = 100 * 1024 * 1024
) -> Iterable[Any]:
    """
    Parallel regex over either:
     - mmap‐sliced byte‐ranges if file_path is a real file
     - or line‐based chunks otherwise.
    """
    
    # importing here to shave off some mseconds from import time if multi not used
    from concurrent.futures import ProcessPoolExecutor, as_completed
    # n_cores = n_cores or os.cpu_count() or 1
    use_mmap = bool(file_path and Path(file_path).is_file())

    file_size = os.path.getsize(file_path)
    #tasks_per_core = 4
    #n_chunks = max( n_cores * tasks_per_core, 1 )
    n_chunks = n_cores * 20
    chunk_size_bytes = math.ceil( file_size / n_chunks )


    if use_mmap:
        # Prepare byte‐ranges & mmap‐worker
        ranges = _compute_byte_ranges(file_path, chunk_size_bytes)
        worker_fn = partial(_rygex_worker_range, pos_val, args)
        executor_kwargs = {
            'initializer': _init_worker,
            'initargs': (file_path,)
        }
        tasks = ranges
    else:
        # Prepare line‐reader & line‐worker
        reader = partial(chunked_line_reader,
                         chunk_size,
                         file_path,
                         sys.stdin if not sys.stdin.isatty() else None)
        worker_fn = partial(_rygex_worker_lines, pos_val, args)
        executor_kwargs = {}
        tasks = list(reader())

    with ProcessPoolExecutor(max_workers=n_cores, **executor_kwargs) as executor:
        futures = [executor.submit(worker_fn, t) for t in tasks]
        for fut in as_completed(futures):
            yield fut.result()
       #     for match in fut.result():
       #         yield match
      #      gc.collect()



class RustParsed(TypedDict):
    file_path: str = None
    start_delim: str = None
    start_index: int = None
    end_delim: str = None
    end_index: int = None
    omit_first: int = None
    omit_last: int = None
    print_line_on_match: bool = False
    case_insensitive: bool = False


def rust_args_parser(args:argparse) -> RustParsed:
    rp = RustParsed()
    if args.file:
        rp['file_path'] = str(args.file)
    if args.start:
        rp['start_delim'] = args.start[0]
        if len(args.start) > 1:
            rp['start_index'] = int(args.start[1])
    if args.end:
        rp['end_delim'] = args.end[0]
        if len(args.end) > 1:
            rp['end_index'] = int(args.end[1])

    if not args.end and args.start and len(args.start) < 2:
        rp['print_line_on_match'] = True

    rp['case_insensitive'] = args.insensitive


    # omit_first logic:
    if args.omitfirst:
        val = int(args.omitfirst[0])
        if val == 0:
            # “0” means strip the *entire* start_delim
            rp['omit_first'] = len(args.start[0])
        else:
            rp['omit_first'] = val

    # omit_last logic:
    if args.omitlast:
        val = int(args.omitlast[0])
        if val == 0 and args.end:
            # “0” means strip the *entire* end_delim
            rp['omit_last'] = len(args.end[0])
        else:
            rp['omit_last'] = val

    if args.omitall:
        if args.start:
            rp['omit_first'] = len(args.start[0])
        if args.end:
            rp['omit_last'] = len(args.end[0])

    # drop any None values so Rust sees only the ones we set
    call_args = {k: v for k, v in rp.items() if v is not None}

    # now call with keyword-args
    return call_args

def counter(pattern_search, args):
    from collections import Counter
    pattern_search_dict = Counter(pattern_search)
    pattern_search_list = []
    for grp_tuple, cnt in pattern_search_dict.items():
        joined = ' '.join(grp_tuple)
        pattern_search_list.append((joined, cnt))
    if pattern_search_list:
        return format_counts(pattern_search_list, args=args)
    else:
        return ['0']


def gen_keys(func: Callable, pattern: str, file: str, split_int: list[int], *args):
    for m in func(pattern, file, *args):
        # Start with the first group
        t = m[split_int[0]]
        # For each subsequent group, prefix with a space
        for idx in split_int[1:]:
            t = t + " " + m[idx]
        yield t

def getting_slice(args_field: list[str]):
    try:
        split_str: list = args_field[1].split(' ')
    # IndexError occurs when entire lines are required
    except IndexError:
        split_str = ['0']
    split_int = [int(i) for i in split_str]
    return split_int



def _chunk_worker(pattern: list, filename: str, start: int, end: int) -> dict[str, int]:
    # gen = regex.from_file_range(pattern, filename, start, end)
    c = Counter()
    # for m in gen:

    split_int = getting_slice(pattern)
    c.update(gen_keys(regex.from_file_range, pattern[0], filename, split_int, start, end))

        # c[m[1]] += 1   # increment count for first capture group
    return dict(c)


def wrapper(args):
    return _chunk_worker(*args)


def make_byte_ranges(filename: str, n_workers: int) -> List[tuple[int,int]]:
    """
    Return a list of `n_workers` (start_byte, end_byte) pairs, covering
    [0 .. file_size) without gaps or overlaps, each chunk beginning
    immediately after a '\n' (except chunk 0 at byte 0) and ending
    immediately after a '\n' (except the final chunk which ends at EOF).
    """
    total = os.path.getsize(filename)
    base, rem = divmod(total, n_workers)

    # 1) Build nominal bounds [0, b1, b2, ..., b_N=total]
    nominal_bounds = [0]
    for i in range(n_workers):
        size = base + (1 if i < rem else 0)
        nominal_bounds.append(nominal_bounds[-1] + size)
    # Now nominal_bounds = [0, b1, b2, ..., b_N]; b₀=0, b_N=total

    # 2) Align every internal bound forward to the next newline
    aligned_bounds = [0] * (n_workers + 1)
    aligned_bounds[0] = 0
    aligned_bounds[-1] = total

    with open(filename, "rb") as f:
        for k in range(1, n_workers):
            start = nominal_bounds[k]
            if start >= total:
                aligned_bounds[k] = total
                continue

            f.seek(start)
            offset = 0
            while True:
                chunk = f.read(8192)
                if not chunk:
                    # EOF reached before any newline
                    aligned_bounds[k] = total
                    break

                idx = chunk.find(b"\n")
                if idx != -1:
                    # Found a newline at byte (start + offset + idx)
                    aligned_bounds[k] = start + offset + idx + 1
                    break

                offset += len(chunk)
                # Loop again until next newline or EOF

    # 3) Build the final (start, end) pairs
    ranges: List[Tuple[int,int]] = []
    for i in range(n_workers):
        s = aligned_bounds[i]
        e = aligned_bounds[i+1]
        if s < e:
            ranges.append((s, e))
        else:
            # If s >= e, that means this worker has nothing to do
            ranges.append((s, s))

    return ranges




def parallel_bytewise_count(pattern: str, filename: str, n_workers: int = None) -> Counter:
    from concurrent.futures import ProcessPoolExecutor, as_completed
    if n_workers is None:
        n_workers = os.cpu_count()

    specs = []
    for (start, end) in make_byte_ranges(filename, n_workers):
        specs.append((pattern, filename, start, end))
    final = Counter()
    with ProcessPoolExecutor(max_workers=n_workers) as exe:
        # “exe.map” only accepts a function and N iterables of arguments
        # We have a list of 4‐tuples, so we use a small lambda to unpack them:
        for partial_dict in exe.map(wrapper, specs):
            final.update(partial_dict)

    return final



def main_seq(python_args_bool=False, args=None):
    '''main sequence for arguments to run'''
    
    if python_args_bool is False:
        args = get_args()

    sense_check(args=args, argTty=sys.stdin.isatty())

    # Initial case-insensitivity check
    # checkFirst, checkLast = omit_check(args=args)
    rp = rust_args_parser(args)
    if args.gen:
        if args.multi:
            counts = parallel_bytewise_count(args.gen, str(args.file), 16)
            return format_counts(list(counts.items()), args)
        else:
            count_dict = Counter()
            # if args.counts:
            split_int = getting_slice(args.gen)
            count_dict.update(gen_keys(regex.FileRegexGen, args.gen[0], str(args.file), split_int))
            pattern_search_list = list(count_dict.items())
            return format_counts(pattern_search_list, args)

    if args.start:

        if args.multi:
            pattern_search = regex.extract_fixed_spans_parallel(**rp)
        else:
            pattern_search = regex.extract_fixed_spans(**rp)
        # Getting input from file or piped input
        # if args.file and Path(args.file).exists():
        #     file_list = unified_input_reader(args.file)
        # elif not sys.stdin.isatty(): # for using piped std input. 
        #     file_list = unified_input_reader()
        # else:
        #     print_err('Input not recognised, check file path or stdin')

        # # check for case-insensitive & initial 'start' search
        # if args.insensitive == False:
        #     pattern_search = normal_search(file_list=file_list,args=args,
        #                                             checkFirst=checkFirst,
        #                                             checkLast=checkLast)
        # else:               
        #     pattern_search = lower_search(file_list=file_list,args=args,
        #                                   checkFirst=checkFirst,
        #                                   checkLast=checkLast)
    # python regex search
    multi = True if args.multi else False

    if args.fixed_string:
        if args.totalcounts:
            return regex.total_count_fixed_str(args.fixed_string[0], rp['file_path'], multi, rp['case_insensitive'])
        if args.multi:
            pattern_search = regex.extract_fixed_lines_parallel(
                file_path=rp['file_path'],
                pattern=args.fixed_string[0],
                case_insensitive=rp['case_insensitive']                
            )
        else:
            pattern_search = regex.extract_fixed_lines(
                file_path=rp['file_path'],
                pattern=args.fixed_string[0],
                case_insensitive=rp['case_insensitive']
            )
    if args.pyreg:
        try:
            pos_val = args.pyreg[1]
        except IndexError: # only if no group arg is added on commandline
            pos_val = '0'
        if args.multi:
            import itertools
            pattern_search = itertools.chain.from_iterable(multi_cpu(args=args, file_path=args.file, pos_val=pos_val, n_cores=args.multi))
        else:
            pattern_search = rygex_mmap(args=args, file_path=args.file, pos_val=pos_val)

    if args.rpyreg:
        if len(args.rpyreg) > 1:
            cg_str: str = args.rpyreg[1]
            cg_list = cg_str.split(' ')
            cg_list = [int(x) for x in cg_list]
        else:
            cg_list = None

        if args.totalcounts:
            return regex.total_count(args.rpyreg[0], str(args.file), multi)

        if args.multi:
            pattern_search = regex.find_joined_matches_in_file_by_line_parallel(args.rpyreg[0], str(args.file), cg_list)
        else:
            pattern_search = regex.find_joined_matches_in_file(args.rpyreg[0], str(args.file), cg_list)

    gc.collect()
    if not pattern_search:
        print('No Pattern Found')
        exit(0)
    # unique search
    if args.unique:
        pattern_search = list(dict.fromkeys(pattern_search))
    # sort search
    if args.counts != True and args.sort:
        test_re = re.compile(r'^[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}$')
        test_ip = test_re.findall(pattern_search[0])
        if args.sort:
            if test_ip:
                import ipaddress
                pattern_search.sort(key=ipaddress.IPv4Address)
            else:
                pattern_search.sort()
        if args.rev:
            if test_ip:
                import ipaddress
                pattern_search.sort(key=ipaddress.IPv4Address, reverse=True)
            else:
                pattern_search.sort(reverse=True)
    # counts search
    if args.counts:
        # from collections import Counter
        pattern_search_tuple = tuple(Counter(pattern_search).items())
        return format_counts(pattern_search_tuple, args=args)
    if args.totalcounts:
        if isinstance(pattern_search, Generator):
            pattern_search = list(pattern_search)
        return [str(len(pattern_search))]
    # lines search
    if args.lines != slice(None, None, None):
        if isinstance(args.lines[0], int):
            pattern_search = [pattern_search[args.lines[0]]]
        else:
            pattern_search = pattern_search[args.lines[0]]
        return pattern_search
    else:
        # [print(i) for i in pattern_search]
        return pattern_search


def main():
    try:
        for line in main_seq():
            print(line)
        # print('\n'.join(main_seq()))
    except KeyboardInterrupt:
        sys.exit(1)

# Run main sequence if name == main.
if __name__ == '__main__':

    # Experimental
    # args = PythonArgs(#pyreg=['\w+\s+DST=(123.12.123.12)\s+\w+', '1'],
    #                     start=['SRC=', 1],
    #                     end=[' DST', 1],
    #                     file='ufw.test',
    #                     lines='1-10',
    #                     # counts=True,
    #                     # sort=True,
    #                     # rev=True,
    #                     # omitfirst=2,
    #                     # omitlast=5,
    #                     omitall=True
    #                     )
    # main_seq(python_args_bool=True, args=args)
    #return_main = main_seq()
    main()

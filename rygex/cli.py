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
from typing import List, Tuple, Any, Callable, Optional
from rygex.utils import print_err
from rygex.args import get_args, PythonArgs
from rygex.python_regex import multi_cpu, rygex_mmap
from rygex.utils import getting_slice


# (1) Define your package version in one place, e.g. in pyproject.toml / setup.cfg
#     so importlib.metadata.version() can pick it up.


# sense checking commandline input.
def sense_check(args: PythonArgs,
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



def format_counts(counts: Sequence[tuple[str,int]], args: PythonArgs) -> list[str]:
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
    if isinstance(args.lines, slice) or isinstance(args.lines, int):
        items = items[args.lines]
    
    if not isinstance(items, list):
        items = [items]

    # Format
    return [f"{k:{padding}}Line-Counts = {v}" for k, v in items]



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


def rust_args_parser(args:PythonArgs) -> dict:
    rp: RustParsed = new_rustparsed()
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
        val = int(args.omitfirst)
        if val == 0 and args.start:
            # “0” means strip the *entire* start_delim
            rp['omit_first'] = len(args.start[0])
        else:
            rp['omit_first'] = val

    # omit_last logic:
    if args.omitlast:
        val = int(args.omitlast)
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




def _chunk_worker(pattern: list[str], filename: str, start: int, end: int) -> dict[str, int]:
    c = Counter()

    split_int = getting_slice(pattern)
    c.update(gen_keys(regex.from_file_range, pattern[0], filename, split_int, start, end))

    return dict(c)


def start_worker(args):
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


def parallel_bytewise_count(pattern: list[str], filename: str, n_workers: int = 1) -> Counter:
    from concurrent.futures import ProcessPoolExecutor

    specs = []
    for (start, end) in make_byte_ranges(filename, n_workers):
        specs.append((pattern, filename, start, end))
    final = Counter()
    with ProcessPoolExecutor(max_workers=n_workers) as exe:
        for partial_dict in exe.map(start_worker, specs):
            final.update(partial_dict)

    return final



def main_seq():
    '''main sequence for arguments to run'''
    pattern_search: list[str] = []
    args = get_args()

    sense_check(args=args, argTty=sys.stdin.isatty())

    rp = rust_args_parser(args)
    if args.gen:
        if args.multi:
            counts = parallel_bytewise_count(args.gen, str(args.file), args.multi)
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

    multi = True if args.multi else False

    if args.fixed_string:
        if args.totalcounts:
            return regex.total_count_fixed_str(args.fixed_string, rp['file_path'], multi, rp['case_insensitive'])
        if args.multi:
            pattern_search = regex.extract_fixed_lines_parallel(
                file_path=rp['file_path'],
                pattern=args.fixed_string,
                case_insensitive=rp['case_insensitive']                
            )
        else:
            pattern_search = regex.extract_fixed_lines(
                file_path=rp['file_path'],
                pattern=args.fixed_string,
                case_insensitive=rp['case_insensitive']
            )
    if args.pyreg:
        if args.multi:
            import itertools
            pattern_search = list(itertools.chain.from_iterable(multi_cpu(args=args, file_path=str(args.file), n_cores=args.multi)))
        else:
            pattern_search = rygex_mmap(args=args, file_path=args.file)

    if args.rpyreg:
        if len(args.rpyreg) > 1:
            cg_str: str = args.rpyreg[1]
            cg_list = cg_str.split(' ')
            cg_list = [int(x) for x in cg_list]
        else:
            cg_list = [0]

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
    if args.lines:
        if isinstance(args.lines, int):
            pattern_search = [pattern_search[args.lines]]
        else:
            pattern_search = pattern_search[args.lines]
        return pattern_search
    else:
        return pattern_search


def main():
    try:
        for line in main_seq():
            print(line)
    except KeyboardInterrupt:
        sys.exit(1)



if __name__ == '__main__':
    main()

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

import re, sys, gc
from typing import Generator
import rygex_ext as regex
from collections import Counter
from rygex.args import get_args
from rygex.python_regex import multi_cpu, rygex_mmap
from rygex.utils import getting_slice
from rygex.validation import sense_check
from rygex.converters import rust_args_parser
from rygex.formatting import format_counts, gen_keys
from rygex.parallel import parallel_bytewise_count


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
        sys.exit(0)
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

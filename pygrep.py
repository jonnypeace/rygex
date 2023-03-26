#!/usr/bin/python3

"""
PYGREP - Python string and regex search
=======================================

SYNOPSIS
========
./pygrep.py [-s keyword/character [position]] | [-p regex [position|all]] [-e keyword/character position] [-i] [-l int|$|$-int|int-int] [-of] [-ol] [-f /path/to/file]

Author and Github
=================
Author: Jonny Peace, email: jonnypeace@outlook.com
Link for further information can be found here...
https://github.com/jonnypeace/pygrep/blob/main/README.md

Description
===========
Python string and regex search made easy. Select characters/keywords from and to sections of a line, further enhance with python regex, and specific lines.
Can accept stdin from a pipe or using the -f|--file flag

OPTIONS
=======
-s  | --start       can be used standlone (without --pyreg) or with --pyreg. [keyword/character [position]]
-e  | --end         is optional. Provides an end to the line you are searching for. [keyword/character position]
-of | --omitfirst   is optional for deleting the first character of your match. No further args required. Only works with --start
-ol | --omitlast    is optional and same as --omitfirst. Only works with --start
-l  | --lines       is optional and to save piping using tail, head or sed. [int|$|$-int|int-int|int-$]
-p  | --pyreg       can be used standlone (without --start) or with --start. [regex [position|all]]
-i  | --insensitive When used, case insensitive search is used. No args required.
-f  | --file        /path/to/file.

Examples
========
 -s can be run with position being equal to all, to capture the start of the line
 ./pygrep.py -s root all -f /etc/passwd                 ## output: root:x:0:0::/root:/bin/bash
 ./pygrep.py -s root 1 -e \: 4 -f /etc/passwd           ## output: root:x:0:0:
 ./pygrep.py -s CRON 1 -e \) 2 -f /var/log/syslog       ## Output: CRON[108490]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
 ./pygrep.py -s jonny 2 -f /etc/passwd                  ## output: jonny:/bin/bash

 without -o
 ./pygrep.py -s \( 1 -e \) 1 -f testfile                ## output: (2nd line, 1st bracket)
 with -of -ol
 ./pygrep.py -s \( 1 -e \) 1 -of -ol -f testfile             ## output: 2nd line, 1st bracket

-p or --pyreg | I recommend consulting the python documentation for python regex using re.
 with -s & -p

 ./pygrep.py -s Feb -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test

 with -p
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test
"""

import argparse
import re
import sys

# sense checking commandline input.
def sense_check(aStart: list=[], aEnd: list=[], aPyreg: list=[], aFile: list=[], aTty: bool=False):
# if not stdin or file, error
    if not aFile and aTty:
        print(f'{colours["fail"]}Requires stdin from somewhere, either from --file or pipe{colours["end"]}', file=sys.stderr)
        exit(1)

    # Removed the required field for start, with the intention to use either start or pyreg, and build a pyreg function
    if not aStart and not aPyreg:
        print(f'{colours["fail"]}This programme requires the --start or --pyreg flag to work properly{colours["end"]}', file=sys.stderr)
        exit(1)

    if aPyreg and len(aPyreg) > 2:
        print(f'{colours["fail"]}--pyreg can only have 2 args... search pattern and option{colours["end"]}', file=sys.stderr)
        exit(1)

    if aStart and len(aStart) > 2:
        print(f'{colours["fail"]}--start has too many arguments, character or word followed by occurent number{colours["end"]}', file=sys.stderr)
        exit(1)
    
    if args.omitfirst == None and args.start == None:
        print(f'{colours["fail"]}error, --omitfirst without --start{colours["end"]}', file=sys.stderr)
        exit(1)

    if args.omitlast == None and args.end == None:
        print(f'{colours["fail"]}error, --omitlast without --end{colours["end"]}', file=sys.stderr)
        exit(1)

    if args.omitall != 'False' and (args.omitfirst != 'False' or args.omitlast != 'False'):
        print(f'{colours["fail"]}error, --omitfirst or --omitlast cant be used with --omitall{colours["end"]}', file=sys.stderr)
        exit(1)

# Lower start seach is case insensitive
def lower_search(file_list: tuple)-> list:
    # If positional number value not set, default to all.
    if len(args.start) < 2:
        args.start.append('all')
    '''If arg.start[1] does not equal 'all'...
    Change arg.start[1] to int, since it will be a string.'''
    if args.start[1] != 'all':
        try:
            iter_start = int(args.start[1])
        except ValueError:
            print(f'{colours["fail"]}Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args{colours["end"]}', file=sys.stderr)
            exit(1)

    # Sense check args.end and ensure 2nd arg is an int
    if args.end:
        try:
            iter_end = int(args.end[1])
            if args.start[0] == args.end[0]:
                iter_end += 1
        except ValueError:
            print(f'{colours["fail"]}ValueError: -e / --end only accepts number values{colours["end"]}', file=sys.stderr)
            exit(1)
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
                    for occur_end in range(iter_start -1):
                        new_index = new_str.casefold().index(lower_str, new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if args.end:
                    new_index = new_str.casefold().index(lower_end)
                    length_end = len(args.end[0])
                    for occur_end in range(iter_end -1):
                        new_index = new_str.casefold().index(lower_end, new_index + 1)
                    new_str = new_str[:new_index + length_end]
                start_end.append(new_str)
                '''ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                so we would want to pass those as well.'''
            except ValueError:
                pass
    return start_end

# Normal start search, case sensitive
def normal_search(file_list: tuple)-> list:
    # If positional number value not set, default to all.
    if len(args.start) < 2:
        args.start.append('all')
    '''If arg.start[1] does not equal 'all'...
    Change arg.start[1] to int, since it will be a string.'''
    if args.start[1] != 'all':
        try:
            iter_start = int(args.start[1])
        except ValueError:
            print(f'{colours["fail"]}Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args{colours["end"]}', file=sys.stderr)
            exit(1)

    # Sense check args.end and ensure 2nd arg is an int
    if args.end:
        try:
            iter_end = int(args.end[1])
            if args.start[0] == args.end[0]:
                iter_end += 1
        except ValueError:
            print(f'{colours["fail"]}ValueError: -e / --end only accepts number values{colours["end"]}', file=sys.stderr)
            exit(1)
    start_end: list= []
    # variables from the optional argument of excluding one character
    for line in file_list:
        if args.start[0] in line:
            try:
                new_str = line
                # Start Arg position and initial string creation.
                if args.start[1] != 'all':
                    init_start = line.index(args.start[0])
                    #init_start = str(line).index(args.start[0])
                    new_str = line[init_start:]
                    new_index = new_str.index(args.start[0])
                    for occur_end in range(iter_start -1):
                        new_index = new_str.index(args.start[0], new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if args.end:
                    new_index = new_str.index(args.end[0])
                    length_end = len(args.end[0])
                    for _ in range(iter_end -1):
                        new_index = new_str.index(args.end[0], new_index + 1)
                    new_str = new_str[:new_index + length_end]
                start_end.append(new_str)
                '''
                ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                so we would want to pass those as well.
                '''
            except ValueError:
                pass
    return start_end

# Py regex search, can be either case sensitive or insensitive
def pygrep_search(pos_val: int=0, insense: bool=True, func_search: tuple=())-> list:
    # if not all, try and make the pos_val an int, if not able then incorrect value, so fail and exit.
    if args.pyreg and len(args.pyreg) > 1 and args.pyreg[1] != 'all':
        try:
            pos_val = int(args.pyreg[1])
        except ValueError:
            print(f'{colours["fail"]}Incorrect input for pyreg - only string allowed to be used with pyreg is "all", or integars. Check args{colours["end"]}', file=sys.stderr)
            exit(1)
    pyreg_last_list: list= []
    test_re = re.compile(args.pyreg[0])
    for line in func_search:        
        pygen_length = len(args.pyreg)
        if insense == True:
            reg_match = test_re.findall(rf'(?i){test_re}', line) # (?i) is for case insensitive
        else:
            reg_match = test_re.findall(rf'{test_re}', line)
        if pygen_length == 2:
            if reg_match:
                if args.pyreg[1] == 'all':
                    pyreg_last_list.append(reg_match)
                else:
                    try:
                        pos_val = int(args.pyreg[1])
                        if reg_match:
                            if len(reg_match[0][pos_val - 1]) != 1:
                                pyreg_last_list.append(reg_match[0][pos_val - 1])
                            else:
                                pyreg_last_list.append(reg_match[pos_val - 1])
                                
                        '''Unboundlocal error due to line in args.pyreg[1] and unassigned pos_val (i.e. index will be a string).
                        indexerror when list exceeds index available
                        valueError due to pos_val being a string'''
                    except (UnboundLocalError, IndexError, ValueError):
                        if args.pyreg[1] == 'all'  or type(pos_val) == int:
                            pass
                        else:
                            print(f'{colours["fail"]}only string allowed to be used with pyreg is "all", check args{colours["end"]}', file=sys.stderr)
                            exit(1)
        elif pygen_length == 1: # defaults to first reg_match in line
            if reg_match:
                pyreg_last_list.append(line)
    return pyreg_last_list

# Arrange lines using args from commandline.
def line_func(start_end: list)-> tuple:
    # args for args.line
    start_end_line = []
    line_num_split = []
    line_num = args.lines[0]
    
    # if last line range
    if '-' in line_num:
        line_range = True
        line_num_split = line_num.split('-')
        if '$' in line_num:
            if line_num_split[0] == '$':
                for rev_count in range(int(line_num_split[1]), 0, -1):
                    start_end_line.append(start_end[-rev_count])
            elif line_num_split[1] == '$':
                line_count = len(start_end) - int(line_num_split[0]) + 2
                for rev_count in range(line_count, 0, -1):
                    start_end_line.append(start_end[-rev_count])
        else:
            high_num = max(int(line_num_split[0]),int(line_num_split[1]))
            for rev_count in range(1, high_num + 1, 1):
                start_end_line.append(start_end[rev_count - 1])
    else: # no range
        # if last line
        line_range = False
        if line_num == '$':
            start_end_line = start_end[-1]
        else:
            line_num = int(line_num)
            start_end_line = start_end[line_num - 1]
    return start_end_line, line_range

# Checking whether the first or last characters will be omitted.
def omit_check(first=None, last=None, aOmitFirst: str='', aOmitLast: str='', aOmitAll: str='')-> tuple:
    if aOmitAll is None:
        first = len(args.start[0])
        last = - len(args.end[0])
        return first, last
    if isinstance(aOmitAll, str) and aOmitAll != 'False':
        try:
            first = int(aOmitAll)
            last = - int(aOmitAll)
            return first, last
        except (ValueError):
            print(f'{colours["fail"]}error, Incorrect arg with --omitall{colours["end"]}', file=sys.stderr)
            exit(1)

    if aOmitFirst is None:
        first = len(args.start[0])
    elif isinstance(aOmitFirst, str) and aOmitFirst != 'False':
        try:
            first = int(aOmitFirst)
        except ValueError:
            print(f'{colours["fail"]}error, Incorrect arg with --omitfirst{colours["end"]}', file=sys.stderr)
            exit(1)

    if aOmitLast is None:
        last = - len(args.end[0])
    elif isinstance(aOmitLast, str) and aOmitLast != 'False':
        try:
            last = - int(aOmitLast)
        except ValueError:
            print(f'{colours["fail"]}error, Incorrect arg with --omitlast{colours["end"]}', file=sys.stderr)
            exit(1)
    return first, last

#Currently, opens a file into a tuple, or takes input from a pipe into a tuple.
if __name__ == '__main__':
    # Setting arg parser args
    pk = argparse.ArgumentParser(prog='pygrep',description='Search files with keywords, characters or python regex')

    pk.add_argument('-s', '--start',
            help='This is the starting string search [keyword|character [position]]',
            type=str,
            required=False,
            nargs='+',
            )

    pk.add_argument('-e', '--end',
            help='end of string search [keyword|character position]',
            type=str,
            nargs=2,
            required=False)

    pk.add_argument('-f', '--file',
            help='filename to string search through',
            type=str,
            required=False)

    pk.add_argument('-i', '--insensitive',
            help='This is just a flag for case insensitive for the start flag, no args required, just flag',
            action='store_true',
            required=False)

    pk.add_argument('-of', '--omitfirst',
            help='optional argument for --start. [int|=start] - Removes characters from --start (left) side of ouput',
            type=str,
            nargs='?',
            default='False',
            required=False)

    pk.add_argument('-ol', '--omitlast',
            help='optional argument for --end. [int|=end] - Removes characters from --end (right) side of ouput',
            type=str,
            nargs='?',
            default='False',
            required=False)
    
    pk.add_argument('-O', '--omitall',
            help='optional argument for --start & --end. [int|=end] - Removes characters from --start & --end of ouput',
            type=str,
            nargs='?',
            default='False',
            required=False)

    pk.add_argument('-p', '--pyreg',
            metavar="[regex [position|all]]",
            help='optional argument, internal pyreg to regex filter output. For instance, a tcpdump SRC ip may be search but DEST ip required',
            type=str,
            nargs='+',
            required=False)

    pk.add_argument('-l', '--lines',
            metavar="'1-10' | '1' | '$-3'",
            help='optional argument to display specific lines, example= ./pygrep.py -s search -l \'$-2\' for last 2 lines. -l \'1-3\' for first 3 lines. -l 6 for the 6th line',
            type=str,
            nargs=1,
            required=False)

    pk.add_argument('-S', '--sort',
            help='This is just a flag for sorting no args required, just flag',
            action='store_true',
            required=False)
    
    pk.add_argument('-u', '--unique',
        help='This is just a flag for unique matches no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument('-c', '--counts',
        help='This is just a flag for unique matches no args required, just flag',
        action='store_true',
        required=False)

    # our variables args parses the function (argparse)
    args = pk.parse_args()
    # colour dictionary for outputing error message to screen
    colours = {'fail': '\033[91m', 'end': '\033[0m'}
    sense_check(aStart=args.start, aEnd=args.end, aPyreg=args.pyreg, aFile=args.file, aTty=sys.stdin.isatty())
    if args.file:
        with open(args.file, 'r') as my_file:
            file_list = tuple(file.strip() for file in my_file)
    elif not sys.stdin.isatty(): # for using piped std input. 
            file_list = tuple(sys.stdin.read().splitlines())
######## 
    # Initial case-insensitivity check
    checkFirst, checkLast = omit_check(aOmitFirst=args.omitfirst, aOmitLast=args.omitlast, aOmitAll=args.omitall)
    if args.start:
        # check for case-insensitive & initial 'start' search
        if args.insensitive == False:
            first_search = normal_search(file_list)
        else:               
            first_search = lower_search(file_list)
        if args.counts: # might require some fine tuning
            from collections import Counter
            count_test = Counter(first_search)
            for key in count_test:
                print(f'{key[checkFirst:checkLast]}\tFound = {count_test[key]}')
            exit(0)
    # start end omits 
    if args.start and not args.pyreg and not args.lines:
        if args.unique:
            first_search = list({ line for line in first_search })
        if args.sort:
            first_search.sort()
        for i in first_search:
            print(i[checkFirst:checkLast])
        exit(0)
########
    # start end omits lines
    if args.start and args.lines and not args.pyreg:
        if args.unique:
            first_search = list({ line for line in first_search })
        if args.sort:
            first_search.sort()
        second_search, line_range = line_func(start_end=first_search)
        if line_range == True:
            for i in second_search:
                print(i[checkFirst:checkLast])
        else:
            print(second_search[checkFirst:checkLast])
        exit(0)
########
    # start end lines omits pyreg 
    if args.start and args.lines and args.pyreg:
        try:
            pos_val = args.pyreg[1]
        except IndexError: # only if no group arg is added on commandline 
            pass
        # regex search
        second_search = pygrep_search(insense=args.insensitive, func_search=tuple(first_search))
        if args.unique:
            second_search = list({ line for line in second_search })
        if args.sort:
            second_search.sort()
        # final line filter search
        third_search, line_range = line_func(start_end=second_search)
        if line_range == True: # multiline
            for i in third_search:
                print(i[checkFirst:checkLast])
        else: # one line only
            print(third_search[checkFirst:checkLast])
        exit(0)
########
    # start end omits pyreg 
    if args.start and not args.lines and args.pyreg:
        try:
            pos_val = args.pyreg[1]
        except IndexError: # only if no group arg is added on commandline 
            pass
        # regex search
        second_search = pygrep_search(insense=args.insensitive, func_search=tuple(first_search))
        if args.unique:
            second_search = list({ line for line in second_search })
        if args.sort:
            second_search.sort()
        # final print loop
        for i in second_search:
            print(i[checkFirst:checkLast])
        exit(0)
########
    # pyreg only
    if args.pyreg and not args.start and not args.lines:
        try:
            pos_val = args.pyreg[1]
        except IndexError: # only if no group arg is added on commandline 
            pass
        # initial regex search
        first_search = pygrep_search(insense=args.insensitive, func_search=file_list)
        if args.unique:
            first_search = list({ line for line in first_search })
        if args.sort:
            first_search.sort()
        if args.counts: # might require some fine tuning
            from collections import Counter
            count_test = Counter(first_search)
            for key in count_test:
                print(f'{key}\tFound = {count_test[key]}')
            exit(0)
        # final loop
        for i in first_search:
            print(i[checkFirst:checkLast])
        exit(0)
########
    # pyreg lines
    if args.pyreg and not args.start and args.lines:
        try:
            pos_val = args.pyreg[1]
        except IndexError: # only if no group arg is added on commandline 
            pass
        # initial regex search
        first_search = pygrep_search(insense=args.insensitive, func_search=file_list)
        # final search
        if args.unique:
            first_search = list({ line for line in first_search })
        if args.sort:
            first_search.sort()
        second_search, line_range = line_func(start_end=first_search)
        if line_range == True: # multiline
            for i in second_search:
                print(i[checkFirst:checkLast])
        else: # one line only
            print(second_search[checkFirst:checkLast])
        exit(0)
########

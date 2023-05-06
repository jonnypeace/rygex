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
 ./pygrep.py -s root all -f /etc/passwd                 ## output: root:x:0:0::/root:/bin/bash
 ./pygrep.py -s root 1 -e \: 4 -f /etc/passwd           ## output: root:x:0:0:
 ./pygrep.py -s CRON 1 -e \) 2 -f /var/log/syslog       ## Output: CRON[108490]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
 ./pygrep.py -s jonny 2 -f /etc/passwd                  ## output: jonny:/bin/bash

 without -of -ol -O
 ./pygrep.py -s \( 1 -e \) 1 -f testfile                ## output: (2nd line, 1st bracket)
 with -of -ol
 ./pygrep.py -s \( 1 -e \) 1 -of -ol -f testfile        ## output:  2nd line, 1st bracket

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
def sense_check(argStart: list=[],
                argEnd: list=[],
                argPyreg: list=[],
                argFile: list=[],
                argOmitfirst: list=[],
                argOmitlast: list=[],
                argOmitall: list=[],
                colours: dict={},
                argTty: bool=False):
# if not stdin or file, error
    if not argFile and argTty:
        print(f'{colours["fail"]}Requires stdin from somewhere, either from --file or pipe{colours["end"]}', file=sys.stderr)
        exit(1)

    # Removed the required field for start, with the intention to use either start or pyreg, and build a pyreg function
    if not argStart and not argPyreg:
        print(f'{colours["fail"]}This programme requires the --start or --pyreg flag to work properly{colours["end"]}', file=sys.stderr)
        exit(1)

    if argPyreg and len(argPyreg) > 2:
        print(f'{colours["fail"]}--pyreg can only have 2 args... search pattern and option{colours["end"]}', file=sys.stderr)
        exit(1)

    if argStart and len(argStart) > 2:
        print(f'{colours["fail"]}--start has too many arguments, character or word followed by occurent number{colours["end"]}', file=sys.stderr)
        exit(1)
    
    if argOmitfirst == None and argStart == None:
        print(f'{colours["fail"]}error, --omitfirst without --start{colours["end"]}', file=sys.stderr)
        exit(1)

    if argOmitlast == None and argEnd == None:
        print(f'{colours["fail"]}error, --omitlast without --end{colours["end"]}', file=sys.stderr)
        exit(1)

    if argOmitall != 'False' and (argOmitfirst != 'False' or argOmitlast != 'False'):
        print(f'{colours["fail"]}error, --omitfirst or --omitlast cant be used with --omitall{colours["end"]}', file=sys.stderr)
        exit(1)

    if not argStart and argPyreg and (argOmitall != 'False' or argOmitfirst != 'False' or argOmitlast !='False'):
        print(f'{colours["fail"]}error, --pyreg not supported with --omitfirst or --omitlast or --omitall{colours["end"]}', file=sys.stderr)
        exit(1)
    
    if not len(argStart) > 1 and ( argOmitall or argOmitfirst or argOmitlast ):
        print(f'{colours["fail"]}error, --start requires numerical index with --omitfirst or --omitlast or --omitall{colours["end"]}', file=sys.stderr)
        exit(1)

def lower_search(file_list: tuple,
                 argStart: list=[],
                 argEnd: list=[],
                 colours: dict={},
                 )-> list:
    '''Lower start seach is case insensitive'''
    # If positional number value not set, default to all.
    if len(argStart) < 2:
        argStart.append('all')
    '''If arg.start[1] does not equal 'all'...
    Change arg.start[1] to int, since it will be a string.'''
    if argStart[1] != 'all':
        try:
            iter_start = int(argStart[1])
        except ValueError:
            print(f'{colours["fail"]}Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args{colours["end"]}', file=sys.stderr)
            exit(1)

    # Sense check args.end and ensure 2nd arg is an int
    if argEnd:
        try:
            iter_end = int(argEnd[1])
            if argStart[0] == argEnd[0]:
                iter_end += 1
        except ValueError:
            print(f'{colours["fail"]}ValueError: -e / --end only accepts number values{colours["end"]}', file=sys.stderr)
            exit(1)
    start_end: list= []
    # variables from the optional argument of excluding one character
    for line in file_list:
        lower_line = line.casefold()
        lower_str = argStart[0].casefold()
        if argEnd:
            lower_end = argEnd[0].casefold()
        if lower_str in lower_line:
            try:
                new_str = line
                # Start Arg position and initial string creation.
                if argStart[1] != 'all':
                    init_start = lower_line.index(lower_str)
                    new_str = line[init_start:]
                    new_index = new_str.casefold().index(lower_str)
                    for _ in range(iter_start -1):
                        new_index = new_str.casefold().index(lower_str, new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if argEnd:
                    new_index = new_str.casefold().index(lower_end)
                    length_end = len(argEnd[0])
                    for _ in range(iter_end -1):
                        new_index = new_str.casefold().index(lower_end, new_index + 1)
                    new_str = new_str[:new_index + length_end]
                start_end.append(new_str)
                '''ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                so we would want to pass those as well.'''
            except ValueError:
                pass
    return start_end

def normal_search(file_list: tuple,
                 argStart: list=[],
                 argEnd: list=[],
                 colours: dict={},
                 )-> list:
    '''Normal start search, case sensitive'''
    # If positional number value not set, default to all.
    if len(argStart) < 2:
        argStart.append('all')
    '''If arg.start[1] does not equal 'all'...
    Change arg.start[1] to int, since it will be a string.'''
    if argStart[1] != 'all':
        try:
            iter_start = int(argStart[1])
        except ValueError:
            print(f'{colours["fail"]}Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args{colours["end"]}', file=sys.stderr)
            exit(1)

    # Sense check args.end and ensure 2nd arg is an int
    if argEnd:
        try:
            iter_end = int(argEnd[1])
            if argStart[0] == argEnd[0]:
                iter_end += 1
        except ValueError:
            print(f'{colours["fail"]}ValueError: -e / --end only accepts number values{colours["end"]}', file=sys.stderr)
            exit(1)
    start_end: list= []
    # variables from the optional argument of excluding one character
    for line in file_list:
        if argStart[0] in line:
            try:
                new_str = line
                # Start Arg position and initial string creation.
                if argStart[1] != 'all':
                    init_start = line.index(argStart[0])
                    new_str = line[init_start:]
                    new_index = new_str.index(argStart[0])
                    for _ in range(iter_start -1):
                        new_index = new_str.index(argStart[0], new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if argEnd:
                    new_index = new_str.index(argEnd[0])
                    length_end = len(argEnd[0])
                    for _ in range(iter_end -1):
                        new_index = new_str.index(argEnd[0], new_index + 1)
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

def pygrep_search(insense: bool=True, func_search: tuple=(),
                  argPyreg: list=[],
                  pos_val: int=0,
                  colours: dict={},
                  )-> list:
    '''Python regex search using --pyreg, can be either case sensitive or insensitive'''
    pyreg_last_list: list= []
    if insense == True:
        test_re = re.compile(argPyreg[0], re.IGNORECASE)
    else:
        test_re = re.compile(argPyreg[0])
    # Splitting the arg for capture groups into a list
    try:
        split_str: list = argPyreg[1].split(' ')
    # IndexError occurs when entire lines are required
    except IndexError:
        pass
    pygen_length = len(argPyreg)
    group_num: int = test_re.groups
    if pygen_length == 1: # defaults to first reg_match in line
        for line in func_search:
            reg_match = test_re.findall(line)
            if reg_match:
                pyreg_last_list.append(line)
    elif pygen_length == 2:
        if argPyreg[1] == 'all':
            if group_num > 1:
                for line in func_search:
                    reg_match = test_re.findall(line)
                    if reg_match:
                        all_group: str = ''
                        for i in reg_match[0]:
                            all_group = all_group + ' ' + i
                        pyreg_last_list.append(all_group[1:])
            if group_num == 1:
                for line in func_search:
                    reg_match = test_re.findall(line)
                    if reg_match:
                        pyreg_last_list.append(reg_match[0])
        elif len(split_str) == 1:
            try:
                pos_val = int(split_str[0])
            except ValueError: #valueError due to pos_val being a string
                print(f'{colours["fail"]}only string allowed to be used with pyreg is "all", check args {split_str}{colours["end"]}', file=sys.stderr)
                exit(1)
            if group_num > 1:
                for line in func_search:
                    reg_match = test_re.findall(line)
                    if reg_match:
                        try:
                            pyreg_last_list.append(reg_match[0][pos_val - 1])
                        #indexerror when list exceeds index available
                        except (IndexError):
                            print(f'{colours["fail"]}Error. Index chosen {split_str} is out of range. Check capture groups{colours["end"]}', file=sys.stderr)
                            exit(1)
            else:
                for line in func_search:
                    reg_match = test_re.findall(line)
                    if reg_match:
                        try:
                            pyreg_last_list.append(reg_match[pos_val - 1])
                        #indexerror when list exceeds index available
                        except (IndexError):
                            print(f'{colours["fail"]}Error. Index chosen {split_str} is out of range. Check capture groups{colours["end"]}', file=sys.stderr)
                            exit(1)
        elif len(split_str) > 1:
            try:
                # Create an int list for regex match iteration.
                int_list: list[int] = [int(i) for i in split_str]
            except ValueError: # Value error when incorrect values for args.
                print(f'{colours["fail"]}Error. Index chosen {split_str} are incorrect. Options are "all" or number value, i.e. "1 2 3" {colours["end"]}', file=sys.stderr)
                exit(1)
            for line in func_search:
                reg_match = test_re.findall(line)     
                if reg_match:
                    all_group = ''
                    try:
                        for i in int_list:
                            all_group = all_group + ' ' + reg_match[0][i - 1]
                        pyreg_last_list.append(all_group[1:])
                    # Indexerror due to incorrect index
                    except IndexError:
                        print(f'{colours["fail"]}Error. Index chosen {split_str} is out of range. Check capture groups{colours["end"]}', file=sys.stderr)
                        exit(1)
    return pyreg_last_list

def line_func(start_end: list | dict,
              colours: dict={},
              argLine: list=[])-> tuple:
    ''''Similar idea from using head and tail, requires --line'''

    # args for args.line
    line_num_split = []
    line_num = argLine[0]

    # Conditional for lines using the counts arg
    if isinstance(start_end, dict):
        start_end_line = dict()
        if '-' in line_num:
            line_range = True
            line_num_split = line_num.split('-')
            if '$' in line_num:
                if line_num_split[0] == '$':
                    max_num = int(line_num_split[1])
                    for num, key in enumerate(reversed(start_end), 1):
                        start_end_line[key] = start_end[key]
                        if num >= max_num:
                            return start_end_line, line_range
                elif line_num_split[1] == '$':
                    line_count = len(start_end) - int(line_num_split[0]) + 1
                    for num, key in enumerate(reversed(start_end), 1):
                        start_end_line[key] = start_end[key]
                        if num >= line_count:
                            return start_end_line, line_range
            else:
                line_count = len(start_end) + 1
                low_num = line_count - max(int(line_num_split[0]),int(line_num_split[1]))
                high_num = line_count - min(int(line_num_split[0]),int(line_num_split[1]))
                if line_count <= max(int(line_num_split[0]),int(line_num_split[1])):
                    print(f'{colours["fail"]}error, not enough lines in file. Try reducing file number{colours["end"]}', file=sys.stderr)
                    exit(1)
                
                for num, key in enumerate(reversed(start_end), 1):
                    if num >= low_num:
                        start_end_line[key] = start_end[key]
                    if num >= high_num:
                        return start_end_line, line_range
        else: # no range
            # if last line
            line_range = False
            if line_num == '$':
                line_count = len(start_end)
                for key in reversed(start_end):
                    start_end_line[key] = start_end[key]
                    return start_end_line, line_range
            else: # specific line
                line_num = int(line_num)
                line_count = len(start_end) + 1
                if line_count <= line_num:
                    print(f'{colours["fail"]}error, not enough lines in file. Try reducing line numbers{colours["end"]}', file=sys.stderr)
                    exit(1)
                for num, key in enumerate(start_end, 1):
                    if num == line_num:
                        start_end_line[key] = start_end[key]
                        return start_end_line, line_range
    # For everything else but not including the counts arg.
    start_end_line_list: list = []
    if '-' in line_num:
        line_range = True
        line_num_split = line_num.split('-')
        if '$' in line_num:
            if line_num_split[0] == '$':
                for rev_count in range(int(line_num_split[1]), 0, -1):
                    start_end_line_list.append(start_end[-rev_count])
            elif line_num_split[1] == '$':
                line_count = len(start_end) - int(line_num_split[0]) + 2
                for rev_count in range(line_count, 0, -1):
                    start_end_line_list.append(start_end[-rev_count])
        else:
            high_num = max(int(line_num_split[0]),int(line_num_split[1]))
            for rev_count in range(1, high_num + 1, 1):
                start_end_line_list.append(start_end[rev_count - 1])
    else: # no range
        # if last line
        line_range = False
        if line_num == '$':
            start_end_line_list = start_end[-1]
        else:
            line_num = int(line_num)
            start_end_line_list = start_end[line_num - 1]
    return start_end_line_list, line_range

def omit_check(first=None, last=None,
               argOmitfirst: str='',
               argOmitlast: str='',
               argOmitall: str='',
               argStart: list=[],
               colours: dict={},
               argEnd: list=[])-> tuple:
    '''Omit characters for --start and --end args'''
    if argOmitall is None:
        try:
            first = len(argStart[0])
            last = - len(argEnd[0])
        except TypeError:
            pass
        return first, last
    if argOmitall != 'False':
        try:
            first = int(argOmitall)
            last = - int(argOmitall)
            return first, last
        except (ValueError):
            print(f'{colours["fail"]}error, Incorrect arg with --omitall{colours["end"]}', file=sys.stderr)
            exit(1)

    if argOmitfirst is None:
        first = len(argStart[0])
    elif argOmitfirst != 'False':
        try:
            first = int(argOmitfirst)
        except ValueError:
            print(f'{colours["fail"]}error, Incorrect arg with --omitfirst{colours["end"]}', file=sys.stderr)
            exit(1)

    if argOmitlast is None:
        last = - len(argEnd[0])
    elif argOmitlast != 'False':
        try:
            last = - int(argOmitlast)
        except ValueError:
            print(f'{colours["fail"]}error, Incorrect arg with --omitlast{colours["end"]}', file=sys.stderr)
            exit(1)
    return first, last

def counts(count_search: list, checkFirst: int=0, checkLast: int=0, argLine: list=[]):
    '''Counts the number of times a line is present and outputs a count, uses the --counts arg'''
    from collections import Counter
    pattern_search = Counter(count_search)
    padding = max([len(z[checkFirst:checkLast]) for z in pattern_search]) + 4
    if argLine:
        pattern_search, _ = line_func(start_end=pattern_search,
                                            argLine=argLine)
        for key in reversed(pattern_search):
            print(f'{key[checkFirst:checkLast]:{padding}}Line-Counts = {pattern_search[key]}')
    else:
        for key in pattern_search:
            print(f'{key[checkFirst:checkLast]:{padding}}Line-Counts = {pattern_search[key]}')
    exit(0)

def get_args():
    '''Setting arg parser args'''
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
            default=None,
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
        help='This is just a flag for counting matches no args required, just flag',
        action='store_true',
        required=False)

    # our variables args parses the function (argparse)
    args = pk.parse_args()

    return args

def main_seq():
    '''main sequence for arguments to run'''
    args = get_args()
    # colour dictionary for outputing error message to screen
    colours = {'fail': '\033[91m', 'end': '\033[0m'}
    sense_check(argStart=args.start,
                argEnd=args.end,
                argPyreg=args.pyreg,
                argFile=args.file,
                argOmitfirst=args.omitfirst,
                argOmitlast=args.omitlast,
                argOmitall=args.omitall,
                colours=colours,
                argTty=sys.stdin.isatty())
    # Getting input from file or piped input
    if args.file:
        with open(args.file, 'r') as my_file:
            file_list = tuple(file.strip() for file in my_file)
    elif not sys.stdin.isatty(): # for using piped std input. 
            file_list = tuple(sys.stdin.read().splitlines())
    # Initial case-insensitivity check
    checkFirst, checkLast = omit_check(argOmitfirst=args.omitfirst,
                                       argOmitlast=args.omitlast,
                                       argOmitall=args.omitall,
                                       argStart=args.start,
                                       argEnd=args.end,
                                       colours=colours)
    if args.start:
        # check for case-insensitive & initial 'start' search
        if args.insensitive == False:
            pattern_search = normal_search(file_list=file_list,
                                        argStart=args.start,
                                        argEnd=args.end,
                                        colours=colours)
        else:               
            pattern_search = lower_search(file_list=file_list,
                                        argStart=args.start,
                                        argEnd=args.end,
                                        colours=colours)
    # python regex search
    if args.pyreg:
        try:
            pos_val = args.pyreg[1]
        except IndexError: # only if no group arg is added on commandline
            pos_val = 0
        # regex search
        pattern_search = pygrep_search(insense=args.insensitive, func_search=tuple(file_list),
                                      argPyreg=args.pyreg, pos_val=pos_val, colours=colours)
    # unique search
    if args.unique:
        pattern_search = list(dict.fromkeys(pattern_search))
    # sort search
    if args.sort:
        pattern_search.sort()
    # counts search
    if args.counts:
        counts(count_search = pattern_search, checkFirst = checkFirst,
               checkLast = checkLast, argLine = args.lines)
    # lines search
    if args.lines:
        pattern_search, line_range = line_func(start_end=pattern_search,
                                                argLine=args.lines, colours=colours)
        if line_range == True: # multiline
            [print(i[checkFirst:checkLast]) for i in pattern_search]
        else: # This prevents a single string from being separated into lines.
           print(pattern_search[checkFirst:checkLast])
    else:
        [print(i[checkFirst:checkLast]) for i in pattern_search]
    
# Run main sequence if name == main.
if __name__ == '__main__':
    main_seq()


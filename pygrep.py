#!/usr/bin/python3

"""
PYGREP - Python string and regex search
=======================================

SYNOPSIS
========
./pygrep.py -s [keyword/character [position]] [-p regex [position|all]] [-e keyword/character position] [-i] [-l int|$|$-int|int-int] [-of] [-ol] [-f /path/to/file]

Author and Github
=================
Author: Jonny Peace, email jonnypeace@outlook.com
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
-l  | --lines       is optional and to save piping using tail, head or sed. [int|$|$-int|int-int]
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
 with -o
 ./pygrep.py -s \( 1 -e \) 1 -o -f testfile             ## output: 2nd line, 1st bracket

-p or --pyreg | I recommend consulting the python documentation for python regex using re.
 with -s & -p

 ./pygrep.py -s Feb -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test

 with -p
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test
"""

import argparse
import re
import sys

# Settings args parser witi the -s option, requiring a string
pk = argparse.ArgumentParser(prog='pygrep',description='Search files with keywords, characters or python regex')

pk.add_argument('-s', '--start',
        help='This is the starting string search <keyword/character> <position>',
        type=str,
        required=False,
        nargs='+',
        )

pk.add_argument('-e', '--end',
        help='end of string search <keyword/character> <position>',
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
        help='optional argument for exc. This will exclude 1 character at the start of string. Right now only works in start and end args',
        action='store_const',
        const='exc',
        required=False)

pk.add_argument('-ol', '--omitlast',
        help='optional argument for exc. This will exclude 1 character at the end of string. Right now only works in start and end args',
        action='store_const',
        const='exc',
        required=False)

pk.add_argument('-p', '--pyreg',
        metavar="'python regex' '[int]' / '[all]'",
        help='optional argument, internal pyreg to regex filter output. For instance, a tcpdump SRC ip may be search but DEST ip required',
        type=str,
        nargs='+',
        required=False)

pk.add_argument('-l', '--lines',
        metavar="'1-10' / '1' / '$-3'",
        help='optional argument to display specific lines, example= ./pygrep.py -s search -l \'$-2\' for last 2 lines. -l \'1-3\' for first 3 lines. -l 6 for the 6th line',
        type=str,
        nargs=1,
        required=False)

# our variables args parses the function (argparse)
args = pk.parse_args()

class gcolours:
    # default values for fail and return of terminal colour
    FAIL = '\033[91m'
    ENDC = '\033[0m'

# if not stdin or file, error
if not args.file and sys.stdin.isatty():
    print(f"{gcolours.FAIL}Requires stdin from somewhere, either from --file or pipe{gcolours.ENDC}")
    exit(1)

# Removed the required field for start, with the intention to use either start or pyreg, and build a pyreg function
if not args.start and not args.pyreg:
    print(f'{gcolours.FAIL}This programme requires the --start or --pyreg flag to work properly{gcolours.ENDC}')
    exit(1)

if args.pyreg and len(args.pyreg) > 2:
    print(f'{gcolours.FAIL}--pyreg can only have 2 args... search pattern and option{gcolours.ENDC}')
    exit(1)

# If positional number value not set, default to all.
if args.start and len(args.start) < 2:
    args.start.append('all')

if args.start and len(args.start) > 2:
    print(f'{gcolours.FAIL}--start has too many arguments, character or word followed by occurent number{gcolours.ENDC}')
    exit(1)

if args.pyreg and len(args.pyreg) > 1 and args.pyreg[1] != 'all':
    try:
        pos_val = int(args.pyreg[1])
    except:
        print(f'{gcolours.FAIL}Incorrect input for pyreg - only string allowed to be used with pyreg is "all", or integars. Check args{gcolours.ENDC}')
        exit(1)

'''Passing a second argument of all for the start option will return output for the start of line
Change arg.start[1] to int, since it will be a string.'''
if args.start and args.start[1] != 'all':
    iter_start = int(args.start[1])

# Sense check args.end and ensure 2nd arg is an int
if args.end:
    try:
        iter_end = int(args.end[1])
    except ValueError:
        print(f'{gcolours.FAIL}ValueError: -e / --end only accepts number values{gcolours.ENDC}')
        exit(1)

# Empty lists which will be populated in the main loops
last_line_list = []
pyreg_last_list = []
start_end = []

# Lower start seach is case insensitive
def lower_search(line, exc_val=0):
    global start_end
    # variables from the optional argument of excluding one character
    lower_line = line.casefold()
    lower_str = args.start[0].casefold()
    if args.end:
        lower_end = args.end[0].casefold()
    if lower_str in lower_line:
        try:
            new_str = str(line)
            # Start Arg position and initial string creation.
            if args.start[1] != 'all':
                init_start = lower_line.index(lower_str)
                new_str = str(line)[init_start:]
                new_index = new_str.casefold().index(lower_str)
                for occur_end in range(iter_start -1):
                    new_index = new_str.casefold().index(lower_str, new_index + 1)
                if args.omitfirst == 'exc':
                    exc_val = 1
                new_str = str(new_str)[new_index + exc_val:]
            # End Arg positions and final string creation
            if args.end:
                new_index = new_str.casefold().index(lower_end)
                length_end = len(args.end[0])
                for occur_end in range(iter_end -1):
                    new_index = new_str.casefold().index(lower_end, new_index + 1)
                if args.omitlast == 'exc':
                    exc_val = -1
                new_str = str(new_str)[:new_index + length_end + exc_val]
            start_end.append(new_str)
            '''ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
            ValueError will probably occur also if you want an instance number from the start search, which does not exist,
            so we would want to pass those as well.'''
        except ValueError:
            pass

# Normal start search, case sensitive
def normal_search(line, exc_val=0):
    global start_end
    # variables from the optional argument of excluding one character
    if args.start[0] in line:
        try:
            new_str = str(line)
            # Start Arg position and initial string creation.
            if args.start[1] != 'all':
                init_start = str(line).index(args.start[0])
                new_str = str(line)[init_start:]
                new_index = new_str.index(args.start[0])
                for occur_end in range(iter_start -1):
                    new_index = new_str.index(args.start[0], new_index + 1)
                if args.omitfirst == 'exc':
                    exc_val = 1
                new_str = str(new_str)[new_index + exc_val:]
            # End Arg positions and final string creation
            if args.end:
                new_index = new_str.index(args.end[0])
                length_end = len(args.end[0])
                for occur_end in range(iter_end -1):
                    new_index = new_str.index(args.end[0], new_index + 1)
                if args.omitlast == 'exc':
                    exc_val = -1
                new_str = str(new_str)[:new_index + length_end + exc_val]
            start_end.append(new_str)
            '''
            ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
            ValueError will probably occur also if you want an instance number from the start search, which does not exist,
            so we would want to pass those as well.
            '''
        except ValueError:
            pass

# Py regex search, can be either case sensitive or insensitive
def pygrep_search(line, pos_val='0', insense=True):
    # variables from the optional argument of excluding one character
    global counts
    global pyreg_last_list

    test_re = args.pyreg[0]
    pygen_length = len(args.pyreg)
    if insense == True:
        reg_match = re.findall(rf'(?i){test_re}', line) # (?i) is for case insensitive
    else:
        reg_match = re.findall(rf'{test_re}', line)
    if pygen_length == 2:
        if reg_match:
            if args.pyreg[1] == 'all':
                print('all')
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
                        print(f'{gcolours.FAIL}only string allowed to be used with pyreg is "all", check args{gcolours.ENDC}')
                        exit(1)
    elif pygen_length == 1: # defaults to first reg_match in line
        if reg_match:
            pyreg_last_list.append(line)

# Arrange lines using args from commandline.
def line_func(start_end):
    # args for args.line
    global start_end_line
    start_end_line = []
    line_num_split = []
    line_num = args.lines[0]
    
    # if last line range
    if '-' in line_num:
        global line_range
        line_range = True
        line_num_split = line_num.split('-')
        if '$' in line_num:
            if line_num_split[0] == '$':
                for rev_count in range(int(line_num_split[1]), 0, -1):
                    start_end_line.append(start_end[-rev_count])
            elif line_num_split[1] == '$':
                for rev_count in range(int(line_num_split[0]), 0, -1):
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

'''
Currently, opens a file and splits it on newline into a list.
The args.start is then searched through each line, and each new indexing is performed
depending on which iteration of the string is required.
Finally the args.end indexing is performed to produce the final string > see functions above.
'''

if args.file:
    with open(args.file, 'r') as my_file:
        file_list = my_file.read()
        file_list_split = file_list.split('\n')
########   
        # start end omits 
        if args.start and not args.pyreg and not args.insensitive and not args.lines:
            for line in file_list_split:
                normal_search(line)
                continue
            for i in start_end:
                print(i)
########
        # start end omits case insensitive
        if args.start and args.insensitive and not args.pyreg and not args.lines:
            for line in file_list_split:
                lower_search(line)
                continue
            for i in start_end:
                print(i)
########
        # start end omits lines
        if args.start and args.lines and not args.pyreg:
            if not args.insensitive:
                # initial start search
                for line in file_list_split:
                    normal_search(line)
                    continue
            else:
                # initial start search
                for line in file_list_split:
                    lower_search(line)
                    continue                
            line_func(start_end)
            if line_range == True:
                for i in start_end_line:
                    print(i)
            else:
                print(start_end_line)
########
        # start end lines omits pyreg 
        if args.start and args.lines and args.pyreg:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass
            # check for case insensitive
            if not args.insensitive:
                test_insense = False
                # initial start search
                for line in file_list_split:
                    normal_search(line)
                    continue
            else:               
                test_insense = True
                # initial start search
                for line in file_list_split:
                    lower_search(line)
                    continue 
            # regex search
            del line
            for line in start_end:
                pygrep_search(line, insense=test_insense)
            # final line filter search
            line_func(start_end=pyreg_last_list)
            if line_range == True: # multiline
                for i in start_end_line:
                    print(i)
            else: # one line only
                print(start_end_line)
########
        # start end omits pyreg 
        if args.start and not args.lines and args.pyreg:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass
            # check for case insensitive
            if not args.insensitive:
                test_insense = False
                # initial start search
                for line in file_list_split:
                    normal_search(line)
                    continue
            else:               
                test_insense = True
                # initial start search
                for line in file_list_split:
                    lower_search(line)
                    continue 
            # regex search
            del line
            for line in start_end:
                pygrep_search(line, insense=test_insense)
            # final print loop
            for i in pyreg_last_list:
                print(i)
########
        # pyreg only
        if args.pyreg and not args.start and not args.lines:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass
            if not args.insensitive:
                test_insense = False
            else:
                test_insense = True
            # initial regex search
            for line in file_list_split:
                pygrep_search(line, insense=test_insense)
            # final loop
            for i in pyreg_last_list:
                print(i)
########
        # pyreg lines
        if args.pyreg and not args.start and args.lines:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass
            if not args.insensitive:
                test_insense = False
            else:
                test_insense = True
            # initial regex search
            for line in file_list_split:
                pygrep_search(line, insense=test_insense)
            # final search
            line_func(start_end=pyreg_last_list)
            if line_range == True: # multiline
                for i in start_end_line:
                    print(i)
            else: # one line only
                print(start_end_line)
########
        my_file.close

######################################################################################

# for using piped std input.
if not sys.stdin.isatty():
########
        # start end omits 
        if args.start and not args.pyreg and not args.insensitive and not args.lines:
            for line in sys.stdin.read().splitlines():
                normal_search(line)
                continue
            for i in start_end:
                print(i)
########
        # start end omits case insensitive
        if args.start and args.insensitive and not args.pyreg and not args.lines:
            for line in sys.stdin.read().splitlines():
                lower_search(line)
                continue
            for i in start_end:
                print(i)
########
        # start end omits lines
        if args.start and args.lines and not args.pyreg:
            if not args.insensitive:
                # initial start search
                for line in sys.stdin.read().splitlines():
                    normal_search(line)
                    continue
            else:
                # initial start search
                for line in sys.stdin.read().splitlines():
                    lower_search(line)
                    continue                
            line_func(start_end)
            if line_range == True:
                for i in start_end_line:
                    print(i)
            else:
                print(start_end_line)
########
        # start end lines omits pyreg 
        if args.start and args.lines and args.pyreg:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass
            # check for case insensitive
            if not args.insensitive:
                test_insense = False
                # initial start search
                for line in sys.stdin.read().splitlines():
                    normal_search(line)
                    continue
            else:               
                test_insense = True
                # initial start search
                for line in sys.stdin.read().splitlines():
                    lower_search(line)
                    continue 
            # regex search
            del line
            for line in start_end:
                pygrep_search(line, insense=test_insense)
            # final line filter search
            line_func(start_end=pyreg_last_list)
            if line_range == True: # multiline
                for i in start_end_line:
                    print(i)
            else: # one line only
                print(start_end_line)
########
        # start end omits pyreg 
        if args.start and not args.lines and args.pyreg:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass            
            # check for case insensitive
            if not args.insensitive:
                test_insense = False
            else:
                test_insense = True
            # initial start search    
            for line in sys.stdin.read().splitlines():
                normal_search(line)
                continue
            # regex search
            del line
            for line in start_end:
                pygrep_search(line, insense=test_insense)
            # final print loop
            for i in pyreg_last_list:
                print(i)
########
        # pyreg only
        if args.pyreg and not args.start and not args.lines:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass
            if not args.insensitive:
                test_insense = False
            else:
                test_insense = True
            # initial regex search
            for line in sys.stdin.read().splitlines():
                pygrep_search(line, insense=test_insense)
            # final loop
            for i in pyreg_last_list:
                print(i)
########
        # pyreg lines
        if args.pyreg and not args.start and args.lines:
            try:
                pos_val = args.pyreg[1]
            except IndexError: # only if no group arg is added on commandline 
                pass
            if not args.insensitive:
                test_insense = False
            else:
                test_insense = True
            # initial regex search
            for line in sys.stdin.read().splitlines():
                pygrep_search(line, insense=test_insense)
            # final search
            line_func(start_end=pyreg_last_list)
            if line_range == True: # multiline
                for i in start_end_line:
                    print(i)
            else: # one line only
                print(start_end_line)
########
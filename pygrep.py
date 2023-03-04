#!/usr/bin/python3

"""
 Under Development
 Things to add...
 * Regex with re module - in progress
 * Adding lines to be displayed - in progress
 * Perhaps substitution like sed

 Examples
 Run script with...
 ./pygrep.py -s <keyword/character> <position> [-e <keyword/character> <position>] -f /path/to/file

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
pk = argparse.ArgumentParser(prog='pygrep',description='search files with keywords or characters')

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
        default='null-or-zero',
        required=False)

pk.add_argument('-f', '--file',
        help='filename to string search through',
        type=str,
        required=False)

pk.add_argument('-o', '--omit',
        help='optional argument for exc. This will exclude 1 character on each side of the string',
        type=str,
        nargs='?',
        const='exc',
        required=False)

pk.add_argument('-i', '--insensitive',
        help='This is just a flag for case insensitive for the start flag, no args required, just flag',
        type=str,
        nargs='?',
        const='True',
        required=False)

#### Temporary holding this until I figure out a weird bug with --omitlast

pk.add_argument('-of', '--omitfirst',
        help='optional argument for exc. This will exclude 1 character at the start of string',
        type=str,
        nargs='?',
        const='exc',
        required=False)

pk.add_argument('-ol', '--omitlast',
        help='optional argument for exc. This will exclude 1 character at the end of string',
        type=str,
        nargs='?',
        const='exc',
        required=False)

pk.add_argument('-p', '--pyreg',
        metavar="'python regex' '[int]' / '[all]' / [line]",
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

pk.add_argument('-c', '--colour',
        #help='optional colour output, colours included are purple, blue, cyan, green, orange, red, white',
        help='CURRENTLY DISABLED',
        type=str,
        nargs=1,
        required=False)

# our variables args parses the function (argparse)
args = pk.parse_args()

class gcolours:

    # default values for fail and return of terminal colour
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    #defining constructor for colour options. Default is orange - this section currently disabled due to issues when used with other programmes.
    def __init__(self, colourOption='ORANGE'):
        
        match colourOption:
            case 'PURPLE':
                self.colour = '\033[95m'
            case 'BLUE':
                self.colour = '\033[94m'
            case 'CYAN':
                self.colour = '\033[96m'
            case 'GREEN':
                self.colour = '\033[92m'
            case 'ORANGE':
                self.colour = '\033[93m'
            case 'RED':
                self.colour = '\033[31m'
            case 'WHITE':
                self.colour = '\033[97m'
            case _:
                print('No match found, try using uppercase')

# The parser automagically returns the value from the commandline - this is the way!

# colour output (not really using for now, as it doesn't play well with other programmes)
if args.colour:
    colourStr = args.colour[0].upper()
    colourPrint = gcolours(colourStr)
else:
    colourPrint = gcolours()

if args.insensitive and not args.insensitive == 'True':
    print(f'{args.insensitive} error. --insensitive has no args')
    exit()

# if not stdin or file, error
if not args.file and sys.stdin.isatty():
    print(f"{gcolours.FAIL}Requires stdin from somewhere, either from --file or pipe{gcolours.ENDC}")
    exit(1)

# Leaving this conditional in until more bug testing carried out with the omit syntax
if args.omitfirst == 'exc' and args.omit == 'exc' or args.omitlast == 'exc' and args.omit == 'exc':
    print(f"{gcolours.FAIL}Only use omitfirst with omitlast, but not with omit{gcolours.ENDC}")
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

if args.pyreg:
    if len(args.pyreg) < 2 or args.pyreg[1] == 'line' or args.pyreg[1] == 'all':
        pass
    else:
        try:
            pos_val = int(args.pyreg[1])
        except:
            print(f'{gcolours.FAIL}Incorrect input for pyreg - only strings allowed to be used with pyreg are "line" and "all", or integars. Check args{gcolours.ENDC}')
            exit(1)

'''Passing a second argument of all for the start option will return output for the start of line
Change arg.start[1] to int, since it will be a string.'''
if args.start and args.start[1] != 'all':
    iter_start = int(args.start[1])

# parse lines if exists
if args.lines:
    line_num = args.lines[0]
    if '-' in line_num:
        line_cond = True
        last_line = False
        last_line_range = False
        line_num_split = line_num.split('-')
        if line_num_split[0] == '$':
            last_line_range = True
    if line_num == '$':
        line_cond = False
        last_line = True
        last_line_range = False
    elif '-' not in line_num:
        line_cond = False
        last_line = False
        last_line_range = False

# Ommiting the argument for end will allow output to end of line, so using default value
# null-or-zero helps with this ommition.
if args.end != 'null-or-zero':
    iter_end = int(args.end[1])

for_pyreg = []
last_line_list = []
pyreg_last_list = []
counts = 0

def lower_search(line):
    # variables from the optional argument of excluding one character
    exc_val = 0
    lower_line = line.casefold()
    lower_str = args.start[0].casefold()
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
                if args.omit == 'exc':
                    exc_val = 1
                if args.omitfirst == 'exc':
                    exc_val = 1
                new_str = str(new_str)[new_index + exc_val:]
            # End Arg positions and final string creation
            if args.end != 'null-or-zero':
                new_index = new_str.casefold().index(lower_end)
                length_end = len(args.end[0])
                for occur_end in range(iter_end -1):
                    new_index = new_str.casefold().index(lower_end, new_index + 1)
                if args.omit == 'exc':
                    exc_val = -1
                if args.omitlast == 'exc':
                    exc_val = -1
                new_str = str(new_str)[:new_index + length_end + exc_val]
            global counts
            counts += 1
            if args.lines and last_line_range == True:
                for_pyreg.append(new_str)
            else:
                if args.lines and line_cond == True:
                    if counts >= int(line_num_split[0]) and counts <= int(line_num_split[1]):
                        for_pyreg.append(new_str)
                        if args.pyreg is None:
                            print(f"{new_str}")
                    else:
                        pass
                elif args.lines and last_line == True:
                    for_pyreg.append(new_str)
                    pass
                elif args.lines and line_cond == False:
                    if counts == int(args.lines[0]):
                        for_pyreg.append(new_str)
                        if args.pyreg is None:
                            print(f"{new_str}")
                else:
                    for_pyreg.append(new_str)
                    if args.pyreg is None:
                        print(f"{new_str}")
                global last_line_str
                try:
                    last_line_str = for_pyreg[-1]
                except IndexError:
                    if not args.lines and not line_num_split[0]:
                        print('problems with indexing') # occurs when range is above 1

                '''ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                so we would want to pass those as well.'''
        except ValueError:
            pass

def normal_search(line):
    # variables from the optional argument of excluding one character
    exc_val = 0
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
                if args.omit == 'exc':
                    exc_val = 1
                if args.omitfirst == 'exc':
                    exc_val = 1
                new_str = str(new_str)[new_index + exc_val:]
            # End Arg positions and final string creation
            if args.end != 'null-or-zero':
                new_index = new_str.index(args.end[0])
                length_end = len(args.end[0])
                for occur_end in range(iter_end -1):
                    new_index = new_str.index(args.end[0], new_index + 1)
                if args.omit == 'exc':
                    exc_val = -1
                if args.omitlast == 'exc':
                    exc_val = -1
                new_str = str(new_str)[:new_index + length_end + exc_val]
            global counts
            counts += 1
            if args.lines and last_line_range == True:
                for_pyreg.append(new_str)
            else:
                if args.lines and line_cond == True:
                    if counts >= int(line_num_split[0]) and counts <= int(line_num_split[1]):
                        for_pyreg.append(new_str)
                        if args.pyreg is None:
                            print(f"{new_str}")
                    else:
                        pass
                elif args.lines and last_line == True:
                    for_pyreg.append(new_str)
                    pass
                elif args.lines and line_cond == False:
                    if counts == int(args.lines[0]):
                        for_pyreg.append(new_str)
                        if args.pyreg is None:
                            print(f"{new_str}")
                else:
                    for_pyreg.append(new_str)
                    if args.pyreg is None:
                        print(f"{new_str}")
                global last_line_str
                try:
                    last_line_str = for_pyreg[-1]
                except IndexError:
                    if not args.lines and not line_num_split[0]:
                        print('problems with indexing') # occurs when range is above 1
                    '''
                    ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                    ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                    so we would want to pass those as well.
                    '''
        except ValueError:
            pass

def pygrep_search(line):
    # variables from the optional argument of excluding one character
    global counts
    global pyreg_last
    global pyreg_last_list
#    pos_val = 0
    test_re = args.pyreg[0]
    pygen_length = len(args.pyreg)
    reg_match = re.findall(rf'(?i){test_re}', line) # (?i) is for case insensitive
    if pygen_length == 2:
        if args.pyreg[1] == 'line':
            if reg_match and args.lines and last_line_range == True:
                pyreg_last_list.append(line)
            else:
                if reg_match and args.lines and line_cond == True:
                    counts += 1
                    if counts >= int(line_num_split[0]) and counts <= int(line_num_split[1]):
                        print(f'{line}')
                elif reg_match and args.lines and last_line == True:
                    counts += 1
                    pyreg_last = line
                elif reg_match and args.lines and line_cond == False:
                    counts += 1
                    if counts == int(args.lines[0]):
                        print(f'{line}')
                elif reg_match:
                    counts += 1
                    print(f'{line}')
        if args.pyreg[1] == 'all':
            if reg_match and args.lines and last_line_range == True:
                pyreg_last_list.append(reg_match)
            else:
                if reg_match and args.lines and line_cond == True:
                    counts += 1
                    if counts >= int(line_num_split[0]) and counts <= int(line_num_split[1]):
                        print(f'{reg_match}')
                elif reg_match and args.lines and last_line == True:
                    counts += 1
                    pyreg_last = reg_match
                elif reg_match and args.lines and line_cond == False:
                    counts += 1
                    if counts == int(args.lines[0]):
                        print(f'{reg_match}')
                elif reg_match:
                    counts += 1
                    print(f'{reg_match}')
        else:
            try:
                pos_val = int(args.pyreg[1])
                if reg_match and args.lines and last_line_range == True:
                    pyreg_last_list.append(reg_match[0][pos_val - 1])
                elif pos_val:
                    if reg_match and args.lines and line_cond == True:
                        counts += 1
                        if counts >= int(line_num_split[0]) and counts <= int(line_num_split[1]):
                            print(reg_match[0][pos_val -1])
                    elif reg_match and args.lines and last_line == True:
                        counts += 1
                        pyreg_last = reg_match[pos_val - 1]
                    elif reg_match and args.lines and line_cond == False:
                        counts += 1
                        if counts == int(args.lines[0]):
                            print(reg_match[0][pos_val -1])
                    elif reg_match:
                        counts += 1
                        print(reg_match[0][pos_val -1])
                '''Unboundlocal error due to line in args.pyreg[1] and unassigned pos_val (i.e. index will be a string).
                indexerror when list exceeds index available
                valueError due to pos_val being a string'''
            except (UnboundLocalError, IndexError, ValueError):
                if args.pyreg[1] == 'line' or args.pyreg[1] == 'all'  or type(pos_val) == int:
                    pass
                else:
                    print(f'{gcolours.FAIL}only strings allowed to be used with pyreg are "line" and "all", check args{gcolours.ENDC}')
                    exit(1)
    elif pygen_length == 1: # defaults to first reg_match in line
        if reg_match and args.lines and last_line_range == True:
            pyreg_last_list.append(reg_match[0][0])
        else:    
            if reg_match and args.lines and line_cond == True:
                counts += 1
                if counts >= int(line_num_split[0]) and counts <= int(line_num_split[1]):
                    print(f'{reg_match[0][0]}')
            elif reg_match and args.lines and last_line == True:
                counts += 1
                pyreg_last = reg_match[0][0]
            elif reg_match and args.lines and line_cond == False:
                counts += 1
                if counts == int(args.lines[0]):
                    print(f'{reg_match[0][0]}')
            elif reg_match:
                counts += 1
                print(f'{reg_match[0][0]}')

# for using piped std input.
if not sys.stdin.isatty():
    for line in sys.stdin.read().splitlines():
        if args.pyreg and not args.start:
            pygrep_search(line)
            continue
        if args.insensitive == 'True':
            lower_search(line)
        else:
            normal_search(line)

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
        counts = 0
        for num, line in enumerate(file_list_split, 0):
            if args.pyreg and not args.start:
                pygrep_search(line)
                continue
            if args.insensitive == 'True':
                lower_search(line)
            else:
                normal_search(line)
        my_file.close

# Last line args and output
if args.lines and last_line == True and args.pyreg is None:
    print(f'{last_line_str}')
if args.pyreg and args.lines and last_line == True:
    print(f'{pyreg_last}')

# Last line ranges
if args.lines and last_line_range == True:
    for rev_count in reversed(range(1, int(line_num_split[1]) + 1, 1)):
        if pyreg_last_list:
            print(f'{pyreg_last_list[-rev_count]}')
        if for_pyreg:
            print(f'{for_pyreg[-rev_count]}')

# matches for args start and args pyreg
if args.pyreg is None or args.lines and last_line_range == True:
    exit()
elif args.start and args.pyreg:
    del line
    test_re = args.pyreg[0]
    pygen_length = len(args.pyreg)
    [
        pygrep_search(line) for line in for_pyreg
    ]



#!/usr/bin/env python3

from typing import Generator
from rygex.printer import print_err


# Old code to get these functions started
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

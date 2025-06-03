#!/usr/bin/env python3
#
import sys

def print_err(msg):
    '''
    Print error messages, to std error and exit with exit code 1.
    '''
    colours = {'fail': '\033[91m', 'end': '\033[0m'}
    print(f'{colours["fail"]}{msg}{colours["end"]}', file=sys.stderr)
    exit(1)

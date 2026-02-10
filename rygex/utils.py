import sys

def print_err(msg):
    '''
    Print error messages, to std error and exit with exit code 1.
    '''
    colours = {'fail': '\033[91m', 'end': '\033[0m'}
    print(f'{colours["fail"]}{msg}{colours["end"]}', file=sys.stderr)
    sys.exit(1)

def getting_slice(args_field: list[str]):
    try:
        split_str: list = args_field[1].split(' ')
    # IndexError occurs when entire lines are required
    except IndexError:
        split_str = []
    split_int = [int(i) for i in split_str]
    return split_int
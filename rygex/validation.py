from rygex.args import PythonArgs
from rygex.utils import print_err

def sense_check(args: PythonArgs, argTty: bool=False):
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
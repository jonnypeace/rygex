from rygex.args import PythonArgs
from rygex.models import RustParsed, new_rustparsed

def rust_args_parser(args: PythonArgs) -> dict:
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
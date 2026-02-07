from typing import Iterable, Literal, TypedDict, Any
import re, mmap, os, math, sys, gc
from pathlib import Path
from dataclasses import dataclass
from rygex.args import PythonArgs
from functools import partial
from rygex.utils import getting_slice, print_err


def grouped_iter(file_data: Iterable[str],test_reg: re.Pattern, int_list=None):
    temp_list: list = []
    for line in file_data:
        reg_match = test_reg.findall(line)
        if reg_match:
            all_group = ''
            if int_list:
                for i in int_list:
                    all_group = all_group + ' ' + reg_match[0][i-1]
            else:
                for i in reg_match[0]:
                    all_group = all_group + ' ' + i
            temp_list.append(all_group[1:])
    return temp_list

def rygex_search(args: PythonArgs, func_search: Iterable[str] = None)-> list:
    '''Python regex search using --pyreg, can be either case sensitive or insensitive'''
    parsed = rygex_parser(args)
    match parsed.pygen_length:
        case 1: # defaults to printing full line if regular expression matches
            for line in func_search:
                reg_match = parsed.test_reg.findall(line)
                if reg_match:
                    parsed.pyreg_last_list.append(line)
        case 2:
            if len(parsed.split_int) == 1:
                if parsed.split_int[0] == 0:
                    for line in func_search:
                        reg_match = parsed.test_reg.findall(line)
                        if reg_match:
                            parsed.pyreg_last_list.append(line)
                else:
                    for line in func_search:
                        reg_match = parsed.test_reg.findall(line)
                        if reg_match:
                            parsed.pyreg_last_list.append(reg_match[0][parsed.split_int[0]-1])
            else:
                parsed.pyreg_last_list = grouped_iter(file_data=func_search, test_reg=parsed.test_reg)

    return parsed.pyreg_last_list



def mmap_reader(file_path: str, regex_pattern: str, criteria: Literal['line', 'match'], insensitive: bool = False): # single threaded

    with open(file_path, 'rb', buffering=0) as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # Compile the regular expression pattern
            pattern = re.compile(regex_pattern.encode('utf-8'), re.IGNORECASE) if insensitive else re.compile(regex_pattern.encode('utf-8'))
            # Search using the pattern, yielding match objects
            match criteria:
                case 'line':
                    for match in pattern.finditer(mm):
                        start = max(0, mm.rfind(b'\n', 0, match.start())+1)
                        end = mm.find(b'\n', match.end())
                        if end == -1:
                            end = len(mm)  # Handle case where the match is in the last line
                        # Append the whole line as a decoded string
                        yield mm[start:end].decode('utf-8')
                case 'match':
                    for match in pattern.finditer(mm):
                        yield match.groups()
                
                case _:
                    print_err('Internal error with criteria matching')

@dataclass
class ParserPyReg:
    test_reg: re.Pattern
    pygen_length: int
    group_num: int
    split_int: list[int]
    pyreg_last_list: list

def rygex_parser(args: PythonArgs):

    test_reg: re.Pattern = re.compile(args.pyreg[0], re.IGNORECASE) if args.insensitive else re.compile(args.pyreg[0])
    # Splitting the arg for capture groups into a list
    split_int = getting_slice(args.pyreg)

    return ParserPyReg(
        test_reg = test_reg,
        split_int = split_int,
        pygen_length = len(args.pyreg),
        group_num = test_reg.groups,
        pyreg_last_list = []
    )

class ReaderArgs(TypedDict):
    file_path: str
    regex_pattern: str
    criteria: Literal['line', 'match']
    insensitive: bool

def reader_args_parser(file_path, args: PythonArgs):
    return ReaderArgs(
        file_path=file_path,
        regex_pattern=args.pyreg[0],
        criteria='match',
        insensitive=args.insensitive
    )


def rygex_mmap(args: PythonArgs, file_path): # single threaded
    '''Python regex search using --pyreg, can be either case sensitive or insensitive'''
    parsed = rygex_parser(args)
    reader_args: ReaderArgs = reader_args_parser(file_path, args)
    line: list[bytes]
    match parsed.pygen_length:
        case 1: # defaults to printing full line if regular expression matches
            reader_args['criteria'] = 'line'
            for line in mmap_reader(**reader_args):
                parsed.pyreg_last_list.append(line)
        case 2:
            if len(parsed.split_int) == 1:
                if parsed.split_int[0] == 0:
                    reader_args['criteria'] = 'line'
                    for line in mmap_reader(**reader_args):
                        parsed.pyreg_last_list.append(line)
                else:
                    for line in mmap_reader(**reader_args):
                        parsed.pyreg_last_list.append(line[parsed.split_int[0]-1].decode())

            elif len(parsed.split_int) > 1:
                for line in mmap_reader(**reader_args):
                    all_group = ''
                    try:
                        for i in parsed.split_int:
                            all_group = all_group + ' ' + line[i - 1].decode()
                        parsed.pyreg_last_list.append(all_group[1:])
                    # Indexerror due to incorrect index
                    except IndexError:
                        print_err(f'Error. Index chosen {parsed.split_int} is out of range. Check capture groups')

    return parsed.pyreg_last_list

# ——— Globals for worker processes ——————————————
_mm: mmap.mmap

def _init_worker(mmap_path: str):
    """Worker initializer: open & mmap the file once, disable GC."""
    global _mm
    f = open(mmap_path, 'rb')
    _mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    gc.disable()

def _rygex_worker_lines(args: Any, lines: list[str]) -> list[Any]:
    return rygex_search(args=args, func_search=lines)

def _rygex_worker_range(args: Any, byte_range: tuple[int,int]) -> list[Any]:
    start, end = byte_range
    chunk = _mm[start:end]
    lines = [ln.decode('utf8', 'ignore') for ln in chunk.splitlines()]
    return rygex_search(args=args, func_search=lines)

def _compute_byte_ranges(file_path: str, chunk_size_bytes: int) -> list[tuple[int,int]]:
    """Split the file into newline‐aligned byte ranges ~chunk_size_bytes."""
    size = os.path.getsize(file_path)
    ranges: list[tuple[int,int]] = []
    with open(file_path, 'rb') as f, \
         mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        offset = 0
        while offset < size:
            end = min(offset + chunk_size_bytes, size)
            mm.seek(end)
            mm.readline()        # advance to end of line
            end = mm.tell()
            ranges.append((offset, end))
            offset = end
    return ranges

# ——— Pure line‐based chunk reader (fallback) ——————
def chunked_line_reader(
    chunk_size: int,
    file_path: str | None = None,
    stdin=None
) -> Iterable[list[str]]:
    """Yield lists of lines (decoded) from file_path or stdin."""
    source = open(file_path, 'r') if file_path else stdin
    if source is None:
        raise ValueError("Need a valid file_path or piped stdin")
    try:
        buf: list[str] = []
        for line in source:
            buf.append(line.rstrip('\n'))
            if len(buf) >= chunk_size:
                yield buf
                buf = []
        if buf:
            yield buf
    finally:
        if file_path:
            source.close()

# ——— multi_cpu that picks the right reader/worker ————
def multi_cpu(
    args: PythonArgs,
    n_cores: int | None = 8,
    file_path: str | None = None,
    # for line‐reader
    chunk_size: int = 10_000,
    # for mmap reader
    chunk_size_bytes: int = 100 * 1024 * 1024
) -> Iterable[Any]:
    """
    Parallel regex over either:
     - mmap‐sliced byte‐ranges if file_path is a real file
     - or line‐based chunks otherwise.
    """
    
    # importing here to shave off some mseconds from import time if multi not used
    from concurrent.futures import ProcessPoolExecutor, as_completed
    # n_cores = n_cores or os.cpu_count() or 1
    use_mmap = bool(file_path and Path(file_path).is_file())

    file_size = os.path.getsize(file_path)
    #tasks_per_core = 4
    #n_chunks = max( n_cores * tasks_per_core, 1 )
    n_chunks = n_cores * 20
    chunk_size_bytes = math.ceil( file_size / n_chunks )


    if use_mmap:
        # Prepare byte‐ranges & mmap‐worker
        ranges = _compute_byte_ranges(file_path, chunk_size_bytes)
        worker_fn = partial(_rygex_worker_range, args)
        executor_kwargs = {
            'initializer': _init_worker,
            'initargs': (file_path,)
        }
        tasks = ranges
    else:
        # Prepare line‐reader & line‐worker
        reader = partial(chunked_line_reader,
                         chunk_size,
                         file_path,
                         sys.stdin if not sys.stdin.isatty() else None)
        worker_fn = partial(_rygex_worker_lines, args)
        executor_kwargs = {}
        tasks = list(reader())

    with ProcessPoolExecutor(max_workers=n_cores, **executor_kwargs) as executor:
        futures = [executor.submit(worker_fn, t) for t in tasks]
        for fut in as_completed(futures):
            yield fut.result()
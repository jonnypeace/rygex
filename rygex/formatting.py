from typing import Sequence, Callable
from collections import Counter
from rygex.args import PythonArgs

def format_counts(counts: Sequence[tuple[str,int]], args: PythonArgs) -> list[str]:
    """
    Given a list of (key, count) tuples from Rust, apply your
    --sort/--rev/--lines logic and return lines like:
      "{key:<{padding}}Line-Counts = {count}"
    """
    if not counts:
        return []

    # Determine padding
    padding = max(len(k) for k, _ in counts) + 4

    # Start with Rust’s sorted list
    items = list(counts)

    # Python-side sort flag (if you still want Python sort)
    if args.sort:
        items.sort(key=lambda kv: kv[1], reverse=True)

    # Reverse if requested
    if args.rev:
        items = list(reversed(items))

    # Apply --lines filtering if requested
    if isinstance(args.lines, slice) or isinstance(args.lines, int):
        items = items[args.lines]
    
    if not isinstance(items, list):
        items = [items]

    # Format
    return [f"{k:{padding}}Line-Counts = {v}" for k, v in items]

def counter(pattern_search, args: PythonArgs):
    pattern_search_dict = Counter(pattern_search)
    pattern_search_list = []
    for grp_tuple, cnt in pattern_search_dict.items():
        joined = ' '.join(grp_tuple)
        pattern_search_list.append((joined, cnt))
    if pattern_search_list:
        return format_counts(pattern_search_list, args=args)
    else:
        return ['0']

def gen_keys(func: Callable, pattern: str, file: str, split_int: list[int], *args):
    for m in func(pattern, file, *args):
        # Start with the first group
        t = m[split_int[0]]
        # For each subsequent group, prefix with a space
        for idx in split_int[1:]:
            t = t + " " + m[idx]
        yield t
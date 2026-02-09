import os
from typing import List, Tuple
from collections import Counter
import rygex_ext as regex
from rygex.utils import getting_slice
from .formatting import gen_keys

def _chunk_worker(pattern: list[str], filename: str, start: int, end: int) -> dict[str, int]:
    c = Counter()

    split_int = getting_slice(pattern)
    c.update(gen_keys(regex.from_file_range, pattern[0], filename, split_int, start, end))

    return dict(c)


def start_worker(args):
    return _chunk_worker(*args)


def make_byte_ranges(filename: str, n_workers: int) -> List[tuple[int,int]]:
    """
    Return a list of `n_workers` (start_byte, end_byte) pairs, covering
    [0 .. file_size) without gaps or overlaps, each chunk beginning
    immediately after a '\n' (except chunk 0 at byte 0) and ending
    immediately after a '\n' (except the final chunk which ends at EOF).
    """
    total = os.path.getsize(filename)
    base, rem = divmod(total, n_workers)

    # 1) Build nominal bounds [0, b1, b2, ..., b_N=total]
    nominal_bounds = [0]
    for i in range(n_workers):
        size = base + (1 if i < rem else 0)
        nominal_bounds.append(nominal_bounds[-1] + size)
    # Now nominal_bounds = [0, b1, b2, ..., b_N]; b₀=0, b_N=total

    # 2) Align every internal bound forward to the next newline
    aligned_bounds = [0] * (n_workers + 1)
    aligned_bounds[0] = 0
    aligned_bounds[-1] = total

    with open(filename, "rb") as f:
        for k in range(1, n_workers):
            start = nominal_bounds[k]
            if start >= total:
                aligned_bounds[k] = total
                continue

            f.seek(start)
            offset = 0
            while True:
                chunk = f.read(8192)
                if not chunk:
                    # EOF reached before any newline
                    aligned_bounds[k] = total
                    break

                idx = chunk.find(b"\n")
                if idx != -1:
                    # Found a newline at byte (start + offset + idx)
                    aligned_bounds[k] = start + offset + idx + 1
                    break

                offset += len(chunk)
                # Loop again until next newline or EOF

    # 3) Build the final (start, end) pairs
    ranges: List[Tuple[int,int]] = []
    for i in range(n_workers):
        s = aligned_bounds[i]
        e = aligned_bounds[i+1]
        if s < e:
            ranges.append((s, e))
        else:
            # If s >= e, that means this worker has nothing to do
            ranges.append((s, s))

    return ranges


def parallel_bytewise_count(pattern: list[str], filename: str, n_workers: int = 1) -> Counter:
    specs = []
    for (start, end) in make_byte_ranges(filename, n_workers):
        specs.append((pattern, filename, start, end))
    final = Counter()
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=n_workers) as exe:
        for partial_dict in exe.map(start_worker, specs):
            final.update(partial_dict)

    return final
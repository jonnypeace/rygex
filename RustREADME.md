# RustREADME

Reference documentation for the Rust extension that powers `rygex_ext`,
exposed to Python via [PyO3](https://pyo3.rs) and built with
[`maturin`](https://www.maturin.rs/).

The extension mixes two layers:

| Layer | Purpose |
|-------|---------|
| **Legacy API** | Original helper classes/functions used by the `rygex` CLI for high-throughput file scanning. |
| **`re`-compatible API** | Drop-in replacements for the most common Python `re` module calls (`search`, `match`, `fullmatch`, `findall`, `finditer`, `sub`, `subn`, `split`, `compile`). |

The `re`-compatible layer is built on the Rust [`regex`](https://docs.rs/regex)
crate and is intended to behave like the Python standard library for the
features it supports.  Unsupported flags (e.g. `re.VERBOSE`, `re.LOCALE`,
`re.ASCII`) are silently ignored so callers can pass the full
`re.IGNORECASE | re.MULTILINE` value through.

---

## Build / install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
maturin develop --release         # editable install + test build
# or:
maturin build --release
pip install --force-reinstall target/wheels/rygex-*.whl
```

Smoke test:

```python
import rygex_ext as rx
m = rx.match(r"(\w+)", "hello world")
print(m.group(0), m.span())        # -> hello (0, 5)
```

---

## Flag constants

The module re-exports the subset of Python `re` flags that map cleanly onto
Rust `regex` inline flags:

| Constant | Value | Inline flag |
|----------|-------|-------------|
| `I` / `IGNORECASE` | 2  | `(?i)` |
| `M` / `MULTILINE`  | 8  | `(?m)` |
| `S` / `DOTALL`     | 16 | `(?s)` |

Any other bits set in a `flags` value are ignored.

---

## `re`-compatible module-level functions

These are exposed alongside the legacy functions so both code paths can be
used interchangeably.  They each compile a fresh internal pattern on every
call; for repeated use, prefer the `PyPattern` returned by
`compile_with_flags`.

| Function | Signature (defaults) | Returns |
|----------|----------------------|---------|
| `compile_with_flags` | `(pattern, flags=0)`                       | `PyPattern` |
| `search_re`          | `(pattern, string, pos=0, endpos=None, flags=0)`    | `PyMatch` |
| `match`              | `(pattern, string, pos=0, endpos=None, flags=0)`    | `PyMatch` |
| `fullmatch_re`       | `(pattern, string, pos=0, endpos=None, flags=0)`    | `PyMatch` |
| `findall_re`         | `(pattern, string, pos=0, endpos=None, flags=0)`    | `list` |
| `finditer_re`        | `(pattern, string, pos=0, endpos=None, flags=0)`    | `PyFindIter` |
| `sub_re`             | `(pattern, repl, string, count=0, flags=0)`         | `str` |
| `subn_re`            | `(pattern, repl, string, count=0, flags=0)`         | `(str, int)` |
| `split_re`           | `(pattern, string, maxsplit=0, flags=0)`            | `list` |
| `purge`              | `()`                                                | `True` (no-op cache, kept for API parity) |

> **Note on `match`**: the legacy `compile`/`search` functions and the
> `re`-compatible `match` both live in the same module.  The new
> `match` returns a `PyMatch`; the original `search` returns the legacy
> `Match`.  Use `PyPattern`/`compile_with_flags` for the new API.

---

## `PyPattern` – compiled pattern

Built with `compile_with_flags(pattern, flags=0)` or obtained from the
module-level helpers above.  Mirrors `re.Pattern`.

### Properties

| Property     | Type  | Notes |
|--------------|-------|-------|
| `pattern`    | `str` | Source pattern string passed to `compile_with_flags`. |
| `flags`      | `int` | The flag int it was compiled with. |
| `groups`     | `int` | Number of capturing groups, excluding group 0. |
| `groupindex` | `dict[str, int]` | Fresh dict mapping named groups to their group number. |

### Methods

| Method                                | Behaviour |
|---------------------------------------|-----------|
| `search(string, pos=0, endpos=None)`  | Returns a `PyMatch` for the first match in `string[pos:endpos]`, or a null `PyMatch` (truthy-null via `is_null` semantics) when no match. |
| `match(string, pos=0, endpos=None)`   | Like `search`, but the match must start at `pos`. |
| `fullmatch(string, pos=0, endpos=None)` | Like `match`, but the match must also end at `endpos`. |
| `findall(string, pos=0, endpos=None)` | Python-style list: 0 groups -> `list[str]`; 1 group -> `list[str \| None]`; N groups -> `list[tuple[str \| None; N]]`. |
| `finditer(string, pos=0, endpos=None)` | Returns a `PyFindIter` yielding `PyMatch` objects. |
| `findall_captures(string, pos=0, endpos=None)` | Each match as a tuple `(full, group1, group2, ...)`. |
| `findall_captures_named(string)`       | Each match as a dict: `{'full', '0', '1', ...}` plus named-group entries. |
| `sub(repl, string, count=0)`           | `repl` may be a `"\\1"`/`"\\g<name>"` template or a callable taking a `PyMatch`. |
| `subn(repl, string, count=0)`          | Same as `sub` but also returns the substitution count. |
| `split(string, maxsplit=0)`           | Splits `string`; captured groups are interleaved between chunks like Python's `re.split`. |
| `is_match(string, pos=0)`              | Cheap boolean check; does not build a `PyMatch`. |
| `count(string)`                        | Non-overlapping match count. |

### Template replacements

`sub`/`subn` accept either a string template or a callable:

```python
pat = rx.compile_with_flags(r"(\w+)=(\d+)")

out = pat.sub(r"\2=\1", "name=42 age=7")          # "42=name 7=age"
out = pat.sub(lambda m: f"{m.group(1).upper()}={m.group(2)}", "name=42")  # "NAME=42"
```

Python-style escapes recognised in templates:
- `\1`, `\2`, ... (numeric backrefs)
- `\g<name>`, `\g<1>` (named/numeric)
- `\\` (literal backslash)

Internally these are rewritten into the Rust `regex` `${name}`/`$1`
expansion syntax.

---

## `PyMatch` – match object

Mirrors `re.Match`.  Holds the byte spans and captured substrings of every
capture group along with the original haystack, `pos`, `endpos`, pattern
and flags, so all standard attributes are available.

### Properties

| Property    | Type             |
|-------------|------------------|
| `string`    | `str`            |
| `pos`       | `int`            |
| `endpos`    | `int`            |
| `lastindex` | `Optional[int]`  |
| `lastgroup` | `Optional[str]`  |
| `pattern`   | `str`            |
| `flags`     | `int`            |

### Group access

| Method                                | Notes |
|---------------------------------------|-------|
| `start(group=None)`                   | Byte offset of the start of `group`; `-1` if not matched. |
| `end(group=None)`                     | Byte offset of the end of `group`; `-1` if not matched. |
| `span(group=None)`                    | `(start, end)` tuple. |
| `group(*args)`                        | No args -> group 0; 1 arg -> that group; N args -> tuple. |
| `groups(default=None)`                | Tuple of groups 1..N, with `default` for unmatched. |
| `groupdict(default=None)`             | Dict of named groups only. |
| `__getitem__(key)`                    | `m[0]`, `m[1]`, `m["name"]`. |
| `__len__()`                           | Number of capturing groups (excl. 0). |
| `__iter__()`                          | Yields groups 1..N. |
| `__eq__(other)`                       | Equal if spans and captured groups match. |
| `__repr__()`                          | `<rygex.Match object; span=(s, e); match='...'>`. |

`group`/`start`/`end`/`span` accept both ints (negative indexing supported,
e.g. `m.group(-1)`) and named-group strings.

### `PyMatchIter`

Returned by `m.__iter__()`.  Yields groups 1..N (group 0 excluded), like
iterating a Python `re.Match`.

### `PyFindIter`

Returned by `finditer`/`Pattern.finditer`.  Pre-materialises the captures
on construction (so the underlying string is owned for the iterator's
lifetime) and yields a fresh `PyMatch` per `__next__`.  Supports `__len__`.

---

## Legacy API

These predate the `re`-compatible layer and are still used by the CLI.

### Classes

#### `Regex`
Minimal compiled pattern returning the legacy `Match`.

```python
pat = rx.compile(r"\d+")
m = pat.search("hello 42")     # -> Match | None
m.start, m.end, m.group        # ints, ints, str
```

#### `Match`
Legacy match object exposing `start`, `end`, `group` as plain attributes
(not methods).  Returned by `Regex.search` and the module-level `search`
function.

#### `RustRegexGen`
```python
RustRegexGen(pattern: str, iterable_of_strings: Iterable[str])
```
Generator that streams one match per call across every input string.  Each
yield is a tuple `(full_match, group_1, group_2, ...)` of `Optional[str]`.

#### `FileRegexGen`
```python
FileRegexGen(pattern: str, filename: str)
```
Memory-maps `filename` and iterates over regex matches directly on the
mmap.  Yields tuples `(full_match, group_1, ...)`.  Useful for very large
files where loading the whole file into a Python `str` is undesirable.

### Functions

| Function | Description |
|----------|-------------|
| `compile(pattern)`                          | Returns a `Regex`. |
| `search(pattern, text)`                     | Returns `Optional[Match]` (legacy). |
| `findall_captures_str(pattern, text)`       | `list[list[Optional[str]]]` per match. |
| `findall_captures_list(pattern, texts)`     | Same, applied to a list of strings. |
| `findall_captures_list_parallel(...)`       | Parallel (rayon) variant of the above. |
| `findall_captures_named_str(pattern, text)` | `list[dict]` per match. |
| `findall_captures_named_list_parallel(...)` | Parallel variant of the named-dict API. |
| `find_joined_matches_in_file(pattern, file_path, groups)` | Joined matches from a file. |
| `find_joined_matches_in_file_by_line_parallel(...)`       | Parallel-by-line joined matches. |
| `find_joined_matches_in_file_by_line_bytes(...)`          | Byte-oriented variant. |
| `find_joined_matches_in_file_by_line_bytes_parallel(...)` | Parallel byte-oriented variant. |
| `extract_fixed_spans(file_path, start_delim, start_index, end_delim, end_index, omit_first, omit_last, print_line_on_match, case_insensitive)` | Span extraction between two delimiters. |
| `extract_fixed_spans_parallel(...)`         | Parallel variant. |
| `extract_fixed_lines(file_path, pattern, case_insensitive)`                 | Lines containing `pattern`. |
| `extract_fixed_lines_parallel(...)`         | Parallel variant. |
| `total_count(pattern, file_path, parallel)` | Count of matching lines, returned as `list[str]`. |
| `total_count_fixed_str(pattern, file_path, parallel, case_insensitive)` | Fixed-string variant of `total_count`. |
| `count_string_occurrences(items)`           | `list[tuple[str, int]]` tally. |
| `from_file_range(pattern, filename, start, end)` | `FileRegexGen` over a byte range. |

---

## Internals (Rust-side helpers)

These live in `src/lib.rs` but are **not** exported to Python:

| Helper                                  | Purpose |
|-----------------------------------------|---------|
| `apply_flags(pattern, flags)`           | Merges Python flag bits into the pattern as `(?ims)`-style inline flags, including merging into an existing leading `(?...)` group. |
| `snap_to_char_boundary(s, idx)`         | Snaps a byte index to the nearest preceding UTF-8 boundary, used to honour `pos`/`endpos` safely. |
| `build_name_to_index(re)`               | Builds the `Vec<(String, usize)>` of named-group mappings. |
| `py_repl_to_rust_repl(repl)`            | Rewrites a Python replacement template (`\1`, `\g<name>`) into Rust `regex` expansion syntax (`$1`, `${name}`). |
| `PyMatch::from_captures(...)`           | Builds a `PyMatch` from a Rust `Captures`, applying `base` to make spans absolute. |
| `PyMatch::null(...)`                    | Builds the null sentinel returned for failed searches. |
| `PyMatch::group_index_opt` / `group_index` | Resolve optional/non-optional Python group keys (int or str) into `usize` indices, including negative indexing. |
| `PyPattern::do_search` / `do_anchored`  | Internal search primitives used by the public `search`/`match`/`fullmatch` methods. |
| `PyPattern::sub_impl`                   | Shared implementation for `sub`/`subn`, handling both template and callable `repl`. |

---

## Testing

The repository ships a pytest suite under `tests/`:

```bash
source .venv/bin/activate
python -m pytest tests/
```

It covers the Python helpers (`tests/test_python_regex*.py`) and the
`rygex_ext` Rust API directly (`tests/test_rygex_ext.py`).

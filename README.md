# RYGEX

**Python (with some Rust) string and regex search tool**

---

## Alpha - Testing Release

This repository contains the alpha (testing) version of the regex_ext library and its accompanying regex cli command‑line interface.

* What's here
  * A core **regex_ext** library written in rust
  * A prototype **regex** command‑line tool which demonstrates functionality.
* Current State
  * The library is functional but not yet production‑ready.
  * Some CLI commands may behave unexpectedly.
* Why Alpha Release
  * Gather feedback from early users and contributors.
  * Identify bugs and usability issues before a stable release.
  * I still have a use case for this library in it's current state.
* What to expect
  * Documentation/README may be incomplete and change as we refine the user experience.
  * Occasional breaking changes while we experiment with design choices.
  * Frequent updates as we stabilize APIs and fix regressions.


## Why RYGEX?

Tools like `grep`, `sed`, `awk`, `tail`, `head` are amazing—but often you find yourself piping one into another to get exactly what you need. **rygex** combines many of their capabilities in a single command-line tool, with an optional regex_ext python library written in rust to improve performance of parsing large amounts of text.

---

## Installation

### Easy

1. Using PyPi
  ```bash
  pip install rygex
  ```
### Build from source

1. Clone the repo and enter
   ```bash
   git clone https://github.com/jonnypeace/rygex.git
   cd rygex
   ```
2. Install Python dependencies  
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Build and install the Rust extension  
   ```bash
    # Recommended in a python virtual environment
    python3 -m venv .venv
    maturin build --release
    pip install target/wheels/rygex-*.whl --force-reinstall
   ```
4. (Optional) If you need to run rygex as root but keep it in your venv, add your venv’s bin/ to secure_path in /etc/sudoers:  
   ```bash
    # Pay attention to the paths of your virtual environment for this bit....
    # In /etc/sudoers (via `visudo`), near the top:
    Defaults    secure_path="/home/YOUR_USERNAME/.venv/bin:/usr/local/sbin:…"

    # Then, in your ~/.bashrc, auto-activate the venv:
    echo 'source "$HOME/.venv/bin/activate"' >> ~/.bashrc
   ```

_Tested on **Python 3.12+** (Ubuntu 24.04, Arch Linux). Other platforms may work but are untested._

---

## Features

- **String search** (`-s`/`--start`, `-e`/`--end`, Rust-accelerated) - under development after using rust
- **Fixed-string grep** (`-F`/`--fixed-string`, Rust) - Under Development
- **Python regex** (`-p`/`--pyreg`) and **Rust regex** (`-rp`/`--rpyreg`) 
- **Omit characters** before/after matches (`-of`, `-ol`, `-O`)
- **Line slicing** (`-l`/`--lines`) as `start:stop[:step]`  
- **Case-insensitive** search (`-i`/`--insensitive`)  
- **Unique**, **sorted**, **reverse** output (`-u`, `-S`, `-r`)  
- **Count** matches and **total** matches (`-c`, `-t`)  
- **Multithreading** (`-m`/`--multi`)  
- Modular Rust library (`rygex_ext`) for Python integration

---

## Usage

```bash
rygex [OPTIONS] -f <FILE>
```

### Required arguments  
You must supply **one** of:
- `-s/--start PATTERN [INDEX] -e/--end PATTERN [INDEX]`
- `-p/--pyreg <REGEX> [GROUP]`
- `-rp/--rpyreg <REGEX> [GROUP]`
- `-F/--fixed-string <PATTERN>`

…and a source:
- `-f/--file <PATH>`
- piped input (e.g. `cat file | rygex -p foo`). Currently, piping only works with -p as i switch support to the rust implementation.

---

### String searches

- **Start + End**  
  ```bash
  rygex --start foo 2 --end bar 1 -f logfile.txt
  ```
  Finds the 2nd occurrence of `foo` up to the 1st `bar`.

- **Omit first/last chars**  
  ```bash
  rygex --start "(" 1 --end ")" 1 -of 0 -ol 0 -f logfile.txt
  ```
  Strips the outer parentheses from the match.

- **Omit all**  
  ```bash
  rygex --start foo --end bar -O -f logfile.txt
  ```
  Removes both `foo` and `bar` from the ends of each match.

---

### Regex searches

- **Python regex**  
  ```bash
  rygex -p '\d{4}-\d{2}-\d{2}' -f data.log
  ```
- **Rust regex** (faster)  
  ```bash
  rygex -rp '\w+@\w+\.\w+' -f emails.txt
  ```

You can supply an optional group index to extract capture groups:
```bash
rygex -p 'User: (\w+)' '1' -f users.log
```

---

### Common options

| Flag                      | Description                                                                              |
|---------------------------|------------------------------------------------------------------------------------------|
| `-i`, `--insensitive`     | Case-insensitive matching                                                               |
| `-l`, `--lines SLICE`     | Line slicing (e.g. `0:5`, `-3:`, `5:10:2`)                                               |
| `-u`, `--unique`          | Show unique matches only                                                                 |
| `-S`, `--sort`            | Sort output (combine with `-r` for reverse)                                              |
| `-c`, `--counts`          | Show per-match counts                                                                    |
| `-t`, `--totalcounts`     | Show total number of matches                                                             |
| `-m [CORES]`, `--multi`   | Multithreading (defaults to all available cores if no number supplied)                   |
| `-v`, `--version`         | Show version and exit                                                                    |

---

## Roadmap

- [ ] Improve and expand docstrings  
- [ ] Refactor into stable 1.0 branch  
- [ ] Add more benchmarks and CI tests  
- [ ] Docker container for easy deployment  
- [ ] Recursive Search through directories, with excludes
- [ ] Improve Match, compile, search and Iterables (not just lists) using rust

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

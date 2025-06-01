#!/usr/bin/env python3
from rich.console import Console
from rich.table   import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TaskProgressColumn,
)

import subprocess, time, gc, datetime, shlex, resource
from typing import Tuple
from multiprocessing import Process, Event, Queue

### Required Pip install Rich


# ─── PATTERNS ──────────────────────────────────────────────────────────────────
PATTERNS = [
    ('ssh 3grp',      r'(\w+\s+\d+\s+[\d:]+).*?Invalid.*?from\s+(\d+\.\d+\.\d+\.\d+)\s+(.*)', False, False, False, True),
    ("1 ip 1grp",     r"(124\.\d+\.124\.\d+)",               False, True, False, False),
    ('rygex -s -e',   r"-s 'DST=' 1 -e ' LEN' 1 -O -Scm",    False, False, False, False),
    (r"dst 1grp",     r"\sDST=([\d\.]+)\s",                  False, True, False, False),
    ("src spt 2grp",  r"SRC=([\d\.]+).*SPT=([\d\.]+)",       False, False, True, False),
    ("fixed str",     r"124.14.124.14",                      True, False, False, False),
    (r'1grp',         r'\w+\s+DST=([\d\.]+)\s+\w+',          False, True, False, False),
]

# ─── TOOL TEMPLATES ────────────────────────────────────────────────────────────
REGEX_TOOLS_TOTALS_1 = [
    # (
    #     "gawk (1grp)",
    #     r"""gawk 'match($0,/{pat}/,a){c[a[1]]++}"""
    #     r"""END{PROCINFO["sorted_in"]="@val_num_desc";"""
    #     r"""for(k in c)printf "%8d %s\n",c[k],k}' ufw.test1"""
    # ),
    # ("sed (1grp) sort | uniq -c",             r"sed -nE 's/.*{pat}.*/\1/p' ufw.test1 | sort | uniq -c"),
    ("ripgrep (-Nocr $1 total only)",         "rg --no-unicode -No {pat} ufw.test1 -cr '$1'"),
    ("grep (-coP total only)",                "grep -coP {pat} ufw.test1"),
    ("rygex (-rp -t total only)",             "rygex -rp {pat} '1' -t -f ufw.test1"),
    ("rygex (-rp -tm total only)",            "rygex -rp {pat} '1' -tm -f ufw.test1"),
    ("perl (-nE totals 1grp)",                r"""perl -nE '$total += () = /{pat}/g; END { say $total }' ufw.test1""")
]
REGEX_TOOLS_TOTALS_2 = [
    # (
    #     "gawk (2grp)",
    #     r"""gawk 'match($0,/{pat}/,a){c[a[1]" "a[2]]++}"""
    #     r"""END{PROCINFO["sorted_in"]="@val_num_desc";"""
    #     r"""for(k in c)printf "%8d %s\n",c[k],k}' ufw.test1"""
    # ),
    # ("sed (2grp) sort | uniq -c",             r"""sed -nE 's/.*{pat}.*/\1 \2/p' ufw.test1 | sort | uniq -c"""),
    ("ripgrep (-Nocr $1 $2 total only)",      "rg --no-unicode -No {pat} ufw.test1 -cr '$1 $2'"),
    ("grep (-coP total only)",                "grep -coP {pat} ufw.test1"),
    ("rygex (-rp -t total only)",             "rygex -rp {pat} '1 2' -t -f ufw.test1"),
    ("rygex (-rp -tm total only)",            "rygex -rp {pat} '1 2' -tm -f ufw.test1"),
    ("perl (-nE totals 2grp)",                r"""perl -nE '$total += () = /{pat}/g; END { say $total }' ufw.test1""")
]

REGEX_TOOLS_COUNTS_1 = [
    ("ripgrep (-Nocr $1 | sort | uniq -c)",   "rg --no-unicode -No {pat} ufw.test1 -r '$1' | sort | uniq -c"),
    ("rygex (-p -Sc)",                        "rygex -p {pat} '1' -Sc -f ufw.test1"),
    ("rygex (-g -Sc)",                        "rygex -g {pat} '1' -Sc -f ufw.test1"),
    ("rygex (-g -Scm)",                       "rygex -g {pat} '1' -Scm -f ufw.test1"),
    ("rygex (-rp -Sc)",                       "rygex -rp {pat} '1' -Sc -f ufw.test1"),
    ("rygex (-p -Scm)",                       "rygex -p {pat} '1' -Sc -m -f ufw.test1"),
    ("rygex (-rp -Scm)",                      "rygex -rp {pat} '1' -Sc -m -f ufw.test1"),
    ("perl (-nE 1 grp)",                      r"""perl -nE '++$c{$1} if /{pat}/; END{ say "$_\t$c{$_}" for sort keys %c }' ufw.test1"""),
]

REGEX_TOOLS_COUNTS_2 = [
    ("ripgrep (-Nocr $1 $2 | sort | uniq -c)","rg --no-unicode -No {pat} ufw.test1 -r '$1 $2' | sort | uniq -c"),
    ("rygex (-p -Sc)",                        "rygex -p {pat} '1 2' -Sc -f ufw.test1"),
    ("rygex (-g -Sc)",                        "rygex -g {pat} '1 2' -Sc -f ufw.test1"),
    ("rygex (-g -Scm)",                       "rygex -g {pat} '1 2' -Scm -f ufw.test1"),
    ("rygex (-rp -Sc)",                       "rygex -rp {pat} '1 2' -Sc -f ufw.test1"),
    ("rygex (-p -Scm)",                       "rygex -p {pat} '1 2' -Scm -f ufw.test1"),
    ("rygex (-rp -Scm)",                      "rygex -rp {pat} '1 2' -Scm -f ufw.test1"),
    ("perl (-nE 2 grp)",                      r"""perl -nE '++$c{"$1 $2"} if /{pat}/; END{ say "$_\t$c{$_}" for sort keys %c }' ufw.test1"""),
]



FIXED_TOOLS = [
    ("ripgrep (fixed)",        "rg -F {pat} ufw.test1"),
    ("grep (fixed)",           "grep -F {pat} ufw.test1"),
    ("rygex (fixed)",          "rygex -F {pat} -f ufw.test1"),
    ("rygex (fixed -m)",       "rygex -F {pat} -m -f ufw.test1"),
    ("perl (fixed)",           r"""perl -lne 'print if index($_, "{pat}") >= 0' ufw.test1""")
]

NEW_TOOLS = [
    ("rygex --start --end --omitall -Scm", "rygex -s 'DST=' 1 -e ' LEN' 1 -O -Scm -f ufw.test1"),
    ("rygex --start --end --omitall -Sc", "rygex -s 'DST=' 1 -e ' LEN' 1 -O -Sc -f ufw.test1"),
]

REGEX_TOOLS_LIMITED = [
    ("ripgrep (-Nocr $1 $2 | sort | uniq -c)","rg --no-unicode -No {pat} ssh_failures_rand_sample.log -r '$1 $2 $3' | sort | uniq -c"),
    ("rygex (-g -Sc)",                        "rygex -g {pat} '1 2 3' -Sc -f ssh_failures_rand_sample.log"),
    ("rygex (-g -Scm)",                       "rygex -g {pat} '1 2 3' -Scm -f ssh_failures_rand_sample.log"),
    ("rygex (-rp -Sc)",                       "rygex -rp {pat} '1 2 3' -Sc -f ssh_failures_rand_sample.log"),
    ("rygex (-p -Scm)",                       "rygex -p {pat} '1 2 3' -Scm -f ssh_failures_rand_sample.log"),
    ("rygex (-rp -Scm)",                      "rygex -rp {pat} '1 2 3' -Scm -f ssh_failures_rand_sample.log"),
    ("perl (-nE 2 grp)",                      r"""perl -nE '++$c{"$1 $2 $3"} if /{pat}/; END{ say "$_\t$c{$_}" for sort keys %c }' ssh_failures_rand_sample.log"""),
]


def run_free_m(stop_event, out_q: Queue):
    mem_list = []
    while not stop_event.is_set():
        result = subprocess.run(['free', '-k'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        headers: list = lines[0].split()
        values  = lines[1].split()
        headers.insert(0, 0)
        memory_info = dict(zip(headers, values))
        mem_list.append(int(memory_info['used']))
        time.sleep(0.1)
    # compute delta in MB and send it back
    mem_use = (max(mem_list) - min(mem_list)) / 1024
    out_q.put(mem_use)


# ─── MEASUREMENT ────────────────────────────────────────────────────────────────
def measure(cmd: str) -> Tuple[float, float, float, str, float]:
    resource.setrlimit(resource.RLIMIT_AS, (-1, -1))
    stop_event = Event()
    out_q      = Queue()
    free_m_proc = Process(target=run_free_m, args=(stop_event, out_q))
    free_m_proc.start()
    w0 = time.perf_counter()
    u0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
    out, err = proc.communicate()
    w1 = time.perf_counter()
    stop_event.set()
    free_m_proc.join()

    # retrieve the memory delta
    if not out_q.empty():
        mem_increase_mb = out_q.get()
    else:
        mem_increase_mb = 0.0

    gc.collect()
    u1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    real = w1 - w0
    user = u1.ru_utime - u0.ru_utime
    sys_ = u1.ru_stime - u0.ru_stime
    rss  = u1.ru_maxrss / 1024.0
    if proc.returncode != 0:
        print(f"\n⚠️  [{cmd}] failed rc={proc.returncode}")
        print("  stdout:", out.strip())
        print("  stderr:", err.strip())
    return real, user, sys_, out, mem_increase_mb

# ─── BENCHMARK + RICH DISPLAY ───────────────────────────────────────────────────
def run_benchmark(key: str, pattern: str, literal: bool, one: bool, two: bool, three: bool):
    console = Console()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.rule(f"[bold]Pattern[/] {key!r} {pattern!r} @ {ts}")

    if literal:
        tools = [FIXED_TOOLS]
    elif one:
        tools = [REGEX_TOOLS_TOTALS_1, REGEX_TOOLS_COUNTS_1]
    elif two:
        tools = [REGEX_TOOLS_TOTALS_2, REGEX_TOOLS_COUNTS_2]
    elif three:
        tools = [REGEX_TOOLS_LIMITED]
    else:
        tools = [NEW_TOOLS]

    safe = shlex.quote(pattern)

    # We'll use a single Rich "task" that we advance for each command,
    # and set its description to the tool name so it overwrites in place.
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        SpinnerColumn(),
        console=console,
        transient=True,    # clear the bar when done
    ) as progress:
        for tool in tools:
            results = []
            task_id = progress.add_task("", total=len(tool))
            for name, tmpl in tool:
                # update the same task: advance + change its description
                progress.update(task_id, advance=1, description=name)

                if name.lower().startswith("perl") or name.startswith('gawk') or name.startswith('sed'):
                    # insert the raw regex into the Perl // literal
                    sub = pattern
                else:
                    # shell-quote for grep/rg/rygex
                    sub = safe

                if tmpl.startswith('gawk') or tmpl.startswith('sed'):
                    sub = sub.replace(r'\d', r'[:digit:]')
                    sub = sub.replace(r'\s', r'[[:space:]]')

                cmd = tmpl.replace("{pat}", sub)
                gc.collect()
                console.print(cmd)
                real, user, sys_, out, memory_increase = measure(cmd)
                results.append((name, real, user, sys_, out, memory_increase))

            # Build and print a Rich table sorted by real time
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Tool",      style="cyan")
            table.add_column("Real (s)",  justify="right")
            table.add_column("User (s)",  justify="right")
            table.add_column("Sys (s)",   justify="right")
            table.add_column("Memory Increase (MB)", justify="right")
            table.add_column("Output", justify="left")

            for name, real, user, sys_, output, memory_increase in sorted(results, key=lambda x: x[1]):
                table.add_row(
                    name,
                    f"{real:8.3f}",
                    f"{user:8.3f}",
                    f"{sys_:7.3f}",
                    f"{memory_increase:8.2f}",
                    f"{output}",
                )

            console.print(table)

# ─── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for key, pat, lit, one, two, three in PATTERNS:
        run_benchmark(key, pat, lit, one, two, three)

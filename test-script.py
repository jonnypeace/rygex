#!/usr/bin/env python3

import subprocess
import time
import gc
from typing import NamedTuple, Literal
import multiprocessing, datetime

class Colour:
    red: str = '\033[91m'
    green: str = '\033[32m'
    end: str = '\033[0m'

def print_colour(msg):
    '''
    Print error messages, to std error and exit with exit code 1.
    '''
    print(f'\n{Colour.red}{msg}{Colour.end}', end=' ')


def markdown_colour(msg, colour: Literal['red', 'green', 'blue']):
    match colour:
        case 'red':
            return f'<span style="color: red;">{msg}</span>'

        case 'green':
            return f'<span style="color: green;">{msg}</span>'

        case 'blue':
            return f'<span style="color: blue;">{msg}</span>'

        case _:
            return msg


def red(msg):
    return f'{Colour.red}{msg}{Colour.end}'

def green(msg):
    return f'{Colour.green}{msg}{Colour.end}'


def run_free_m(stop_event):
    mem_list: list = []
    while not stop_event.is_set():
        result = subprocess.run(['free', '-k'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        headers = lines[0].split()
        values = lines[1].split()
        headers.insert(0,0)
        # Create a dictionary from the headers and values
        memory_info = dict(zip(headers, values))
        mem_list.append(int(memory_info['used']))
        if result.returncode == 0:
            continue
        else:
            print(f'Command failed with return code {result.returncode}')
        time.sleep(0.1) 
    mem_use = (max(mem_list) - min(mem_list)) / 1024
    print(f'* free -k Total System Memory Increase, Converted to MB: {mem_use:.2f} MB')
    return 

def timer_run(grp, description, command):
    print(f'\n# Group {grp}: {description}\n')
    #print_colour(f'Group {grp}: {description}\n\n')
    #print(f'{Colour.green}*** {command}{Colour.end}\n')
    print(f'```{command}```\n')
    def run_command():
        process = subprocess.Popen(f'/usr/bin/time -v {command}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout, stderr

    gc.collect()
    stop_event = multiprocessing.Event()
    free_m_process = multiprocessing.Process(target=run_free_m, args=(stop_event,))
    free_m_process.start()
    start_time = time.time()
    stdout, stderr = run_command()
    end_time = time.time()
    stop_event.set()
    free_m_process.join()
    gc.collect()
    exec_time = end_time - start_time

    print(f'* Python Subprocess Execution time: {exec_time:.2f} seconds')
    time_data = stderr.decode().splitlines()

    metrics = ['\tUser time (seconds)', '\tSystem time (seconds)', '\tPercent of CPU this job got',
               '\tElapsed (wall clock) time (h:mm:ss or m:ss)', '\tMaximum resident set size (kbytes)']

    for data in time_data:
        for metric in metrics:
            if metric in data:
                if 'Maximum resident set size' in metric:
                    mb = int(data.split(' ')[-1]) / 1024
                    print('*', end=' ')
                    [ print(i.strip(), end=' ') for i in data.split(' ')[:-2] ]
                    print(f'(MBytes): {mb:.2f}')
                else:
                    print(f'* {data.strip()}')

    # print(green(f'\nResult:\n{stdout.decode()}'))
    print(f'\nResult:\n```\n{stdout.decode()}```')

# List of tuples with group, description and command
commands = [
    (1,
    "pygrep: Regex search DST with digit dot pattern, single threaded", 
     r"./pygrep/cli.py -p '\sDST=([\d\.]+)\s' '1' -Sc -f ufw.test1"),
    
    (1,
    "pygrep: Regex search DST with digit dot pattern and multithreaded (12) count", 
     r"./pygrep/cli.py -p '\sDST=([\d\.]+)\s' '1' -m12 -Sc -f ufw.test1"),
    
    (2,
    "pygrep: String Search Between SRC= and DST in UFW log using pygrep", 
     r"./pygrep/cli.py -s 'SRC=' 1 -e ' DST' 1 -O -Sc -f ufw.test1"),

    (2,
    "pygrep: SRC to DST pattern match", 
     r"./pygrep/cli.py -p 'SRC=([\d\.]+)\s+DST' all -Sc -f ufw.test1"),
    
    (2,
    "rg: search SRC to DST pattern", 
     r"rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -cr '$1'"),
    
    (2,
    "rg: search SRC to DST pattern, but with similar output", 
     r"rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | sort | uniq -c"),
   
    (3,
    "rg: search DST with specific IP", 
     r"rg --no-unicode -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1"),
    
    (3,
    "pygrep: DST with specific IP", 
     r"./pygrep/cli.py -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1"),
    
    (3,
    "pygrep: DST with specific IP multithreaded (12)", 
     r"./pygrep/cli.py -p '\s+DST=(124.14.124.14)' 1 -m12 -f ufw.test1"),
    
    (3,
    "pygrep: DST with specific IP multithreaded (4)", 
     r"./pygrep/cli.py -p '\s+DST=(124.14.124.14)' 1 -m4 -f ufw.test1"),
    
    (4,
    "rg: String rg search specific IP", 
     r"rg -No -F '124.14.124.14' ufw.test1"),
    
    (4,
    "pygrep: String Search DST ending with specific IP", 
     r"./pygrep/cli.py -s ' DST=' 1 -e '124.14.124.14' 1 -of 5 -f ufw.test1"),
    
    (5,
    "pygrep: DST with another specific IP", 
     r"./pygrep/cli.py -p '\s+DST=(123.12.123.12)' 1 -Sc -f ufw.test1"),
    
    (5,
    "pygrep: DST with another specific IP and multithreaded (12) count", 
     r"./pygrep/cli.py -p '\s+DST=(123.12.123.12)' 1 -m12 -Sc -f ufw.test1"),
    
    (5,
    "rg: search exact DST match builtin count", 
     r"rg --no-unicode -No '\s+DST=(123.12.123.12)' -cr '$1' ufw.test1"),
    
    (5,
    "pygrep: DST exact match pattern", 
     r"./pygrep/cli.py -p ' DST=(123\.12\.123\.12)' all -Sc -f ufw.test1"),
    
    (5,
    "rg: search DST exact match with builtin count", 
     r"rg -No ' DST=(123\.12\.123\.12)' -cr '$1' ufw.test1"),
    
    (6,
    "pygrep: fixed string search specific IP", 
     r"./pygrep/cli.py -p '124\.14\.124\.14' -f ufw.test1"),
    
    (6,
    "rg: fixed string search specific IP", 
     r"rg -F '124.14.124.14' ufw.test1"),
    
    (6,
    "grep: fixed string search specific IP", 
     r"grep -F '124.14.124.14' ufw.test1"),
    
    (6,
    "pygrep: fixed string search specific IP", 
     r"./pygrep/cli.py -s '124.14.124.14' -f ufw.test1"),
    
    (7,
    "pygrep: Struggles Here. Previous Result 100Sec", 
     r"./pygrep/cli.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -Sc -f ufw.test1"),
    
    (7,
    "pygrep: Lets try with multithreading (12). Previous Result 100Sec", 
     r"./pygrep/cli.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m12 -Sc -f ufw.test1"),
    
    (7,
    "rg: very good performance by comparison", 
     r"rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -cr '$1' ufw.test1"),
    
    (7,
    "rg: same as above, BUT to get the similat output...", 
     r"rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -r '$1' ufw.test1 | sort | uniq -c"),
    
    (8,
    "rg: Wildcard . Searches", 
     r"rg --no-unicode -No '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' -cr '$1' ufw.test1"),
    
    (8,
    "pygrep: Wildcard . Searches", 
     r"./pygrep/cli.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -Sc -f ufw.test1"),
    
    (8,
    "pygrep: Wildcard . Searches multithreaded (12)", 
     r"./pygrep/cli.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -m12 -Sc -f ufw.test1"),
    
    (9,
    "rg: wildcard .* with unicode", 
     r"rg --no-unicode -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1"),
    
    (9,
    "rg: wildcard .*", 
     r"rg -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1"),
    
    (9,
    "pygrep: .* Previous result 11.8s", 
     r"./pygrep/cli.py -p '.*DST=(123.12.123.12).*' 1 -Sc -f ufw.test1"),
    
    (10,
    "rg: 2 capture group regex with wildcard in the middle", 
    r"rg -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1"),
    
    (10,
    "rg: 2 capture group regex --no-unicode with wildcard in the middle", 
     r"rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1"),
    
    (10,
    "rg: 2 capture group regex --no-unicode with wildcard in the middle, but unix tool similar output", 
     r"rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -r '$1 $2' ufw.test1 | sort | uniq -c"),
    
    (10,
    "pygrep: 2 capture group regex with wildcard in the middle", 
     r"./pygrep/cli.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' '1 2' -Sc -f ufw.test1"),
    
    (10,
    "pygrep: 2 capture group regex with wildcard in the middle using all", 
     r"./pygrep/cli.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' 'all' -Sc -f ufw.test1")
]

def versions(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr

for cmd in ('/usr/bin/rg --version', '/usr/bin/python --version'):
    print('\n')
    stdout, stderr = versions(cmd)
    for line in stdout.decode().splitlines():
        print(line)
    for line in stderr.decode().splitlines():
        print(line)

print('\n')

num = -1
now = datetime.datetime.now()
print('Updated:',now.strftime("%d-%m-%Y %H:%M:%S"))
# Loop through the list and call the timer_run function
for grp, description, command in commands:
    if num != grp:
        print('\n############################################################################')
        num = grp
    timer_run(grp, description, command)
    gc.collect()


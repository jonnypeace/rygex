# pygrep
## Python string and regex search

 Under Development
 Things to add...
 * Better Documentation...
 * Regex with re module - in progress, possibly worthy of a beta
 * Adding lines to be displayed - in progress, possibly worthy of a beta

 Examples
 Run script with...
 ```
 ./pygrep.py -s <keyword/character> <position> [-e <keyword/character> <position>] -f /path/to/file

 -s can be run with position being equal to all, to capture the start of the line, this is default if no position provided
 
 ./pygrep.py -s root all -f /etc/passwd                 ## output: root:x:0:0::/root:/bin/bash
 ./pygrep.py -s root 1 -e \: 4 -f /etc/passwd           ## output: root:x:0:0:
 ./pygrep.py -s CRON 1 -e \) 2 -f /var/log/syslog       ## Output: CRON[108490]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
 ./pygrep.py -s jonny 2 -f /etc/passwd                  ## output: jonny:/bin/bash

 without -ol -of (only works with --start, not --pyreg)
 ./pygrep.py -s \( 1 -e \) 1 -f testfile                ## output: (2nd line, 1st bracket)
 with -ol -of (only works with --start, not --pyreg)
 ./pygrep.py -s \( 1 -e \) 1 -ol -of -f testfile             ## output: 2nd line, 1st bracket

-p or --pyreg | I recommend consulting the python documentation for python regex using re.
 
 with -s (--start) & -p (--pyreg)
 ./pygrep.py -s Feb -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test

 with --pyreg (-p)
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=(123.12.123.12)' all -f ufw.test =>  because SRC and DST are in 2 groups using (), all will show both groups
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=(123.12.123.12)' 1 -f ufw.test => This will show the SRC ip enclosed () as the first group

with -i (--insensitive) = case insensitive, this doesn't require much, just needs to be included if required. Works with --start and --pyreg
./pygrep.py -p 'src=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -f ufw.test

with --lines (-l) Note: $ is an end of line character. Enclose in single quotes ''
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l '$-4' -f ufw.test => last 4 lines
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l '$' -f ufw.test => last line
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l '1-4' -f ufw.test => lines 1-4
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l 1 -f ufw.test => first line


```

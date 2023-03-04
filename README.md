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

 -s can be run with position being equal to all, to capture the start of the line
 
 ./pygrep.py -s root all -f /etc/passwd                 ## output: root:x:0:0::/root:/bin/bash
 ./pygrep.py -s root 1 -e \: 4 -f /etc/passwd           ## output: root:x:0:0:
 ./pygrep.py -s CRON 1 -e \) 2 -f /var/log/syslog       ## Output: CRON[108490]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
 ./pygrep.py -s jonny 2 -f /etc/passwd                  ## output: jonny:/bin/bash

 without -o
 ./pygrep.py -s \( 1 -e \) 1 -f testfile                ## output: (2nd line, 1st bracket)
 with -o
 ./pygrep.py -s \( 1 -e \) 1 -o -f testfile             ## output: 2nd line, 1st bracket

-p or --pyreg | I recommend consulting the python documentation for python regex using re.
 with -s & -p

 ./pygrep.py -s Feb -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test

 with -p
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test
```

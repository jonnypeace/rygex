#!/bin/bash

echo '001: -s and -e with -O on big file'
time ./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -f ufw.test1 | wc -l
echo '001 complete'

echo '002: -p -m on big file'
time ./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m 16 -f ufw.test1 | wc -l
echo '002 complete'

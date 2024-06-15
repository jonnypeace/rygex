#!/bin/bash

printf '\n%s\n' '001: -s and -e with -O on big file'
if time ./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -f ufw.test1 | wc -l; then
	printf '%s\n\n' '001 complete'
fi

printf '\n%s\n' '002: -p -m 12 on big file'
if time ./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m 12 -f ufw.test1 | wc -l; then
	printf '%s\n\n' '002 complete'
fi

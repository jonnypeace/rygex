#!/bin/bash

printf '\n%s\n' '001: String Search using -s and -e with -O on ufw.test1'
if time ./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -Sc -f ufw.test1; then
	printf '%s\n\n' '001 complete'
fi

printf '\n%s\n' '002: -p "\w+\s+DST=(123.12.123.12)\s+\w+" -m 12 multithreaded on ufw.test1'
if time ./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m 12 -Sc -f ufw.test1; then
	printf '%s\n\n' '002 complete'
fi


printf '\n%s\n' '003: -p "\sDST=([\d\.]+)\s" single threaded on ufw.test1'
if time ./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -Sc -f ufw.test1; then
	printf '%s\n\n' '003 complete'
fi

printf '\n%s\n' '004: -p "\sDST=([\d\.]+)\s" multi (12) threaded on ufw.test1'
if time ./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -m12 -Sc -f ufw.test1; then
	printf '%s\n\n' '003 complete'
fi
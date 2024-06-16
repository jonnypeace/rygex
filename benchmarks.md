
############################################################################

# Group 1: pygrep: Regex search DST with digit dot pattern, single threaded

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 777.18 MB
* Python Subprocess Execution time: 13.16 seconds
* User time (seconds): 12.60
* System time (seconds): 0.55
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.16
* Maximum resident set size (MBytes): 3520.38

Result:
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1


# Group 1: pygrep: Regex search DST with digit dot pattern and multithreaded (12) count

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2189.99 MB
* Python Subprocess Execution time: 12.57 seconds
* User time (seconds): 25.55
* System time (seconds): 12.30
* Percent of CPU this job got: 301%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.56
* Maximum resident set size (MBytes): 2082.18

Result:
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1


############################################################################

# Group 2: pygrep: String Search Between SRC= and DST in UFW log using pygrep

```./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 792.62 MB
* Python Subprocess Execution time: 12.06 seconds
* User time (seconds): 11.34
* System time (seconds): 0.70
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.05
* Maximum resident set size (MBytes): 780.12

Result:
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830


# Group 2: pygrep: SRC to DST pattern match

```./pygrep.py -p 'SRC=([\d\.]+)\s+DST' all -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 792.21 MB
* Python Subprocess Execution time: 5.27 seconds
* User time (seconds): 4.76
* System time (seconds): 0.50
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.27
* Maximum resident set size (MBytes): 3520.50

Result:
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830


# Group 2: rg: search SRC to DST pattern

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -cr '$1'```

* free -k Total System Memory Increase, Converted to MB: 17.90 MB
* Python Subprocess Execution time: 2.84 seconds
* User time (seconds): 2.63
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.83
* Maximum resident set size (MBytes): 2746.50

Result:
11129400


# Group 2: rg: search SRC to DST pattern, but with similar output

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 26.87 MB
* Python Subprocess Execution time: 19.14 seconds
* User time (seconds): 17.45
* System time (seconds): 0.21
* Percent of CPU this job got: 96%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:18.26
* Maximum resident set size (MBytes): 2746.88

Result:
 556470 157.240.225.34
  61830 62.233.50.245
10511100 79.124.59.134


############################################################################

# Group 3: rg: search DST with specific IP

```rg --no-unicode -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 13.96 MB
* Python Subprocess Execution time: 3.42 seconds
* User time (seconds): 3.22
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:03.42
* Maximum resident set size (MBytes): 2746.50

Result:
124.14.124.14


# Group 3: pygrep: DST with specific IP

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 32.19 MB
* Python Subprocess Execution time: 24.04 seconds
* User time (seconds): 23.84
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:24.03
* Maximum resident set size (MBytes): 2753.62

Result:
124.14.124.14


# Group 3: pygrep: DST with specific IP multithreaded (12)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m12 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1989.81 MB
* Python Subprocess Execution time: 12.15 seconds
* User time (seconds): 40.69
* System time (seconds): 11.54
* Percent of CPU this job got: 430%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.14
* Maximum resident set size (MBytes): 1878.02

Result:
124.14.124.14


# Group 3: pygrep: DST with specific IP multithreaded (4)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m4 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2289.25 MB
* Python Subprocess Execution time: 13.18 seconds
* User time (seconds): 36.80
* System time (seconds): 12.04
* Percent of CPU this job got: 370%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.17
* Maximum resident set size (MBytes): 2228.73

Result:
124.14.124.14


############################################################################

# Group 4: rg: String rg search specific IP

```rg -No -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 10.88 MB
* Python Subprocess Execution time: 0.38 seconds
* User time (seconds): 0.15
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.50

Result:
124.14.124.14


# Group 4: pygrep: String Search DST ending with specific IP

```./pygrep.py -s ' DST=' 1 -e '124.14.124.14' 1 -of 5 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 25.54 MB
* Python Subprocess Execution time: 10.73 seconds
* User time (seconds): 10.27
* System time (seconds): 0.45
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:10.72
* Maximum resident set size (MBytes): 13.12

Result:
124.14.124.14


############################################################################

# Group 5: pygrep: DST with another specific IP

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 796.85 MB
* Python Subprocess Execution time: 26.87 seconds
* User time (seconds): 26.29
* System time (seconds): 0.56
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:26.86
* Maximum resident set size (MBytes): 3520.38

Result:
123.12.123.12    Line-Counts = 11129399


# Group 5: pygrep: DST with another specific IP and multithreaded (12) count

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2311.54 MB
* Python Subprocess Execution time: 13.22 seconds
* User time (seconds): 44.88
* System time (seconds): 12.04
* Percent of CPU this job got: 430%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.21
* Maximum resident set size (MBytes): 2194.44

Result:
123.12.123.12    Line-Counts = 11129399


# Group 5: rg: search exact DST match builtin count

```rg --no-unicode -No '\s+DST=(123.12.123.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 21.61 MB
* Python Subprocess Execution time: 6.15 seconds
* User time (seconds): 5.93
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:06.14
* Maximum resident set size (MBytes): 2746.50

Result:
11129399


# Group 5: pygrep: DST exact match pattern

```./pygrep.py -p ' DST=(123\.12\.123\.12)' all -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 786.48 MB
* Python Subprocess Execution time: 5.40 seconds
* User time (seconds): 4.81
* System time (seconds): 0.58
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.40
* Maximum resident set size (MBytes): 3520.50

Result:
123.12.123.12    Line-Counts = 11129399


# Group 5: rg: search DST exact match with builtin count

```rg -No ' DST=(123\.12\.123\.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 24.11 MB
* Python Subprocess Execution time: 1.42 seconds
* User time (seconds): 1.25
* System time (seconds): 0.16
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.42
* Maximum resident set size (MBytes): 2746.50

Result:
11129399


############################################################################

# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -p '124\.14\.124\.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 23.36 MB
* Python Subprocess Execution time: 1.18 seconds
* User time (seconds): 0.96
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.17
* Maximum resident set size (MBytes): 2753.75

Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0


# Group 6: rg: fixed string search specific IP

```rg -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 11.58 MB
* Python Subprocess Execution time: 0.38 seconds
* User time (seconds): 0.17
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.38

Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0


# Group 6: grep: fixed string search specific IP

```grep -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 7.29 MB
* Python Subprocess Execution time: 0.83 seconds
* User time (seconds): 0.60
* System time (seconds): 0.22
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.83
* Maximum resident set size (MBytes): 2.38

Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0


# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -s '124.14.124.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 13.00 MB
* Python Subprocess Execution time: 2.36 seconds
* User time (seconds): 1.94
* System time (seconds): 0.41
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.36
* Maximum resident set size (MBytes): 13.25

Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0


############################################################################

# Group 7: pygrep: Struggles Here. Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 803.18 MB
* Python Subprocess Execution time: 78.21 seconds
* User time (seconds): 77.65
* System time (seconds): 0.54
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:18.20
* Maximum resident set size (MBytes): 3520.25

Result:
123.12.123.12    Line-Counts = 11129399


# Group 7: pygrep: Lets try with multithreading (12). Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2969.64 MB
* Python Subprocess Execution time: 20.52 seconds
* User time (seconds): 171.74
* System time (seconds): 13.04
* Percent of CPU this job got: 900%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:20.51
* Maximum resident set size (MBytes): 2841.85

Result:
123.12.123.12    Line-Counts = 11129399


# Group 7: rg: very good performance by comparison

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 39.59 MB
* Python Subprocess Execution time: 8.87 seconds
* User time (seconds): 8.67
* System time (seconds): 0.18
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.86
* Maximum resident set size (MBytes): 2746.50

Result:
11129399


# Group 7: rg: same as above, BUT to get the similat output...

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -r '$1' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 31.51 MB
* Python Subprocess Execution time: 49.08 seconds
* User time (seconds): 47.94
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:48.16
* Maximum resident set size (MBytes): 2746.62

Result:
11129399 123.12.123.12


############################################################################

# Group 8: rg: Wildcard . Searches

```rg --no-unicode -No '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 27.42 MB
* Python Subprocess Execution time: 12.69 seconds
* User time (seconds): 12.50
* System time (seconds): 0.18
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.69
* Maximum resident set size (MBytes): 2746.38

Result:
11129399


# Group 8: pygrep: Wildcard . Searches

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 774.63 MB
* Python Subprocess Execution time: 51.37 seconds
* User time (seconds): 50.84
* System time (seconds): 0.51
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:51.36
* Maximum resident set size (MBytes): 3520.12

Result:
123.12.123.12    Line-Counts = 11129399


# Group 8: pygrep: Wildcard . Searches multithreaded (12)

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2701.12 MB
* Python Subprocess Execution time: 16.09 seconds
* User time (seconds): 107.97
* System time (seconds): 12.75
* Percent of CPU this job got: 750%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:16.08
* Maximum resident set size (MBytes): 2594.66

Result:
123.12.123.12    Line-Counts = 11129399


############################################################################

# Group 9: rg: wildcard .* with unicode

```rg --no-unicode -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 31.12 MB
* Python Subprocess Execution time: 11.18 seconds
* User time (seconds): 10.97
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.18
* Maximum resident set size (MBytes): 2746.50

Result:
11129399


# Group 9: rg: wildcard .*

```rg -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 30.00 MB
* Python Subprocess Execution time: 11.36 seconds
* User time (seconds): 11.15
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.35
* Maximum resident set size (MBytes): 2746.38

Result:
11129399


# Group 9: pygrep: .* Previous result 11.8s

```./pygrep.py -p '.*DST=(123.12.123.12).*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 796.68 MB
* Python Subprocess Execution time: 7.21 seconds
* User time (seconds): 6.68
* System time (seconds): 0.52
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:07.20
* Maximum resident set size (MBytes): 3520.88

Result:
123.12.123.12    Line-Counts = 11129399


############################################################################

# Group 10: rg: 2 capture group regex with wildcard in the middle

```rg -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 20.12 MB
* Python Subprocess Execution time: 8.67 seconds
* User time (seconds): 8.47
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.66
* Maximum resident set size (MBytes): 2746.25

Result:
11129400


# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 28.08 MB
* Python Subprocess Execution time: 8.58 seconds
* User time (seconds): 8.37
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.58
* Maximum resident set size (MBytes): 2746.38

Result:
11129400


# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle, but unix tool similar output

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -r '$1 $2' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 33.83 MB
* Python Subprocess Execution time: 92.25 seconds
* User time (seconds): 90.84
* System time (seconds): 0.29
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:31.15
* Maximum resident set size (MBytes): 2746.50

Result:
 556470 157.240.225.34 443
  61830 62.233.50.245 51914
10511100 79.124.59.134 44991


# Group 10: pygrep: 2 capture group regex with wildcard in the middle

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' '1 2' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 943.93 MB
* Python Subprocess Execution time: 9.55 seconds
* User time (seconds): 8.99
* System time (seconds): 0.55
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:09.55
* Maximum resident set size (MBytes): 3691.00

Result:
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830


# Group 10: pygrep: 2 capture group regex with wildcard in the middle using all

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' 'all' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 955.86 MB
* Python Subprocess Execution time: 8.91 seconds
* User time (seconds): 8.23
* System time (seconds): 0.66
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.90
* Maximum resident set size (MBytes): 3690.88

Result:
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830


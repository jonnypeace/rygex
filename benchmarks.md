
############################################################################

# Group 1: pygrep: Regex search DST with digit dot pattern, single threaded

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 794.00 MB
* Python Subprocess Execution time: 13.21 seconds
* User time (seconds): 12.63
* System time (seconds): 0.57
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.21
* Maximum resident set size (MBytes): 3520.62

Result:
```
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
```

# Group 1: pygrep: Regex search DST with digit dot pattern and multithreaded (12) count

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2240.59 MB
* Python Subprocess Execution time: 12.66 seconds
* User time (seconds): 26.18
* System time (seconds): 12.29
* Percent of CPU this job got: 303%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.66
* Maximum resident set size (MBytes): 2142.96

Result:
```
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
```

############################################################################

# Group 2: pygrep: String Search Between SRC= and DST in UFW log using pygrep

```./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 786.54 MB
* Python Subprocess Execution time: 12.09 seconds
* User time (seconds): 11.37
* System time (seconds): 0.70
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.08
* Maximum resident set size (MBytes): 780.00

Result:
```
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830
```

# Group 2: pygrep: SRC to DST pattern match

```./pygrep.py -p 'SRC=([\d\.]+)\s+DST' all -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 787.09 MB
* Python Subprocess Execution time: 5.28 seconds
* User time (seconds): 4.73
* System time (seconds): 0.53
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.27
* Maximum resident set size (MBytes): 3520.50

Result:
```
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830
```

# Group 2: rg: search SRC to DST pattern

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -cr '$1'```

* free -k Total System Memory Increase, Converted to MB: 16.04 MB
* Python Subprocess Execution time: 2.74 seconds
* User time (seconds): 2.54
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.73
* Maximum resident set size (MBytes): 2746.38

Result:
```
11129400
```

# Group 2: rg: search SRC to DST pattern, but with similar output

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 27.77 MB
* Python Subprocess Execution time: 19.30 seconds
* User time (seconds): 17.57
* System time (seconds): 0.26
* Percent of CPU this job got: 96%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:18.43
* Maximum resident set size (MBytes): 2747.00

Result:
```
 556470 157.240.225.34
  61830 62.233.50.245
10511100 79.124.59.134
```

############################################################################

# Group 3: rg: search DST with specific IP

```rg --no-unicode -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 14.50 MB
* Python Subprocess Execution time: 3.48 seconds
* User time (seconds): 3.27
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:03.47
* Maximum resident set size (MBytes): 2746.50

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 32.54 MB
* Python Subprocess Execution time: 24.01 seconds
* User time (seconds): 23.80
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:24.01
* Maximum resident set size (MBytes): 2753.62

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP multithreaded (12)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m12 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1912.94 MB
* Python Subprocess Execution time: 12.03 seconds
* User time (seconds): 40.61
* System time (seconds): 11.46
* Percent of CPU this job got: 433%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.02
* Maximum resident set size (MBytes): 1802.08

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP multithreaded (4)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m4 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2196.73 MB
* Python Subprocess Execution time: 13.12 seconds
* User time (seconds): 37.49
* System time (seconds): 11.91
* Percent of CPU this job got: 376%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.11
* Maximum resident set size (MBytes): 2135.81

Result:
```
124.14.124.14
```

############################################################################

# Group 4: rg: String rg search specific IP

```rg -No -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 11.05 MB
* Python Subprocess Execution time: 0.38 seconds
* User time (seconds): 0.16
* System time (seconds): 0.21
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.38

Result:
```
124.14.124.14
```

# Group 4: pygrep: String Search DST ending with specific IP

```./pygrep.py -s ' DST=' 1 -e '124.14.124.14' 1 -of 5 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 18.12 MB
* Python Subprocess Execution time: 10.84 seconds
* User time (seconds): 10.49
* System time (seconds): 0.34
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:10.83
* Maximum resident set size (MBytes): 13.12

Result:
```
124.14.124.14
```

############################################################################

# Group 5: pygrep: DST with another specific IP

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 784.23 MB
* Python Subprocess Execution time: 29.03 seconds
* User time (seconds): 28.42
* System time (seconds): 0.60
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:29.03
* Maximum resident set size (MBytes): 3520.62

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: pygrep: DST with another specific IP and multithreaded (12) count

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2610.21 MB
* Python Subprocess Execution time: 13.35 seconds
* User time (seconds): 45.48
* System time (seconds): 12.18
* Percent of CPU this job got: 432%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.34
* Maximum resident set size (MBytes): 2491.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: rg: search exact DST match builtin count

```rg --no-unicode -No '\s+DST=(123.12.123.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 31.79 MB
* Python Subprocess Execution time: 6.16 seconds
* User time (seconds): 5.94
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:06.16
* Maximum resident set size (MBytes): 2746.50

Result:
```
11129399
```

# Group 5: pygrep: DST exact match pattern

```./pygrep.py -p ' DST=(123\.12\.123\.12)' all -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 778.30 MB
* Python Subprocess Execution time: 5.48 seconds
* User time (seconds): 4.90
* System time (seconds): 0.56
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.47
* Maximum resident set size (MBytes): 3520.50

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: rg: search DST exact match with builtin count

```rg -No ' DST=(123\.12\.123\.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 11.41 MB
* Python Subprocess Execution time: 1.39 seconds
* User time (seconds): 1.22
* System time (seconds): 0.15
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.38
* Maximum resident set size (MBytes): 2746.62

Result:
```
11129399
```

############################################################################

# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -p '124\.14\.124\.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 18.46 MB
* Python Subprocess Execution time: 1.11 seconds
* User time (seconds): 0.91
* System time (seconds): 0.18
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.10
* Maximum resident set size (MBytes): 2753.50

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: rg: fixed string search specific IP

```rg -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 7.40 MB
* Python Subprocess Execution time: 0.38 seconds
* User time (seconds): 0.16
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.38

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: grep: fixed string search specific IP

```grep -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 8.32 MB
* Python Subprocess Execution time: 0.84 seconds
* User time (seconds): 0.60
* System time (seconds): 0.23
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.83
* Maximum resident set size (MBytes): 2.38

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -s '124.14.124.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 10.70 MB
* Python Subprocess Execution time: 2.36 seconds
* User time (seconds): 1.90
* System time (seconds): 0.45
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.36
* Maximum resident set size (MBytes): 13.00

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

############################################################################

# Group 7: pygrep: Struggles Here. Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 780.12 MB
* Python Subprocess Execution time: 79.17 seconds
* User time (seconds): 78.64
* System time (seconds): 0.52
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:19.16
* Maximum resident set size (MBytes): 3520.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 7: pygrep: Lets try with multithreading (12). Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2885.71 MB
* Python Subprocess Execution time: 20.49 seconds
* User time (seconds): 172.10
* System time (seconds): 13.62
* Percent of CPU this job got: 906%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:20.48
* Maximum resident set size (MBytes): 2774.70

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 7: rg: very good performance by comparison

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 31.23 MB
* Python Subprocess Execution time: 8.85 seconds
* User time (seconds): 8.63
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.84
* Maximum resident set size (MBytes): 2746.38

Result:
```
11129399
```

# Group 7: rg: same as above, BUT to get the similat output...

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -r '$1' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 32.41 MB
* Python Subprocess Execution time: 49.28 seconds
* User time (seconds): 48.14
* System time (seconds): 0.26
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:48.41
* Maximum resident set size (MBytes): 2746.75

Result:
```
11129399 123.12.123.12
```

############################################################################

# Group 8: rg: Wildcard . Searches

```rg --no-unicode -No '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 26.30 MB
* Python Subprocess Execution time: 12.49 seconds
* User time (seconds): 12.28
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.49
* Maximum resident set size (MBytes): 2746.38

Result:
```
11129399
```

# Group 8: pygrep: Wildcard . Searches

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.89 MB
* Python Subprocess Execution time: 54.10 seconds
* User time (seconds): 53.54
* System time (seconds): 0.54
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:54.09
* Maximum resident set size (MBytes): 3520.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 8: pygrep: Wildcard . Searches multithreaded (12)

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2859.12 MB
* Python Subprocess Execution time: 16.15 seconds
* User time (seconds): 108.55
* System time (seconds): 12.03
* Percent of CPU this job got: 746%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:16.14
* Maximum resident set size (MBytes): 2734.24

Result:
```
123.12.123.12    Line-Counts = 11129399
```

############################################################################

# Group 9: rg: wildcard .* with unicode

```rg --no-unicode -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 30.03 MB
* Python Subprocess Execution time: 11.09 seconds
* User time (seconds): 10.92
* System time (seconds): 0.16
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.08
* Maximum resident set size (MBytes): 2746.50

Result:
```
11129399
```

# Group 9: rg: wildcard .*

```rg -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 24.91 MB
* Python Subprocess Execution time: 11.40 seconds
* User time (seconds): 11.23
* System time (seconds): 0.16
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.39
* Maximum resident set size (MBytes): 2746.25

Result:
```
11129399
```

# Group 9: pygrep: .* Previous result 11.8s

```./pygrep.py -p '.*DST=(123.12.123.12).*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.01 MB
* Python Subprocess Execution time: 7.22 seconds
* User time (seconds): 6.67
* System time (seconds): 0.53
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:07.22
* Maximum resident set size (MBytes): 3520.88

Result:
```
123.12.123.12    Line-Counts = 11129399
```

############################################################################

# Group 10: rg: 2 capture group regex with wildcard in the middle

```rg -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 14.25 MB
* Python Subprocess Execution time: 8.69 seconds
* User time (seconds): 8.49
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.69
* Maximum resident set size (MBytes): 2746.50

Result:
```
11129400
```

# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 27.49 MB
* Python Subprocess Execution time: 8.64 seconds
* User time (seconds): 8.38
* System time (seconds): 0.24
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.63
* Maximum resident set size (MBytes): 2746.12

Result:
```
11129400
```

# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle, but unix tool similar output

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -r '$1 $2' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 35.25 MB
* Python Subprocess Execution time: 91.57 seconds
* User time (seconds): 90.16
* System time (seconds): 0.29
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:30.46
* Maximum resident set size (MBytes): 2746.75

Result:
```
 556470 157.240.225.34 443
  61830 62.233.50.245 51914
10511100 79.124.59.134 44991
```

# Group 10: pygrep: 2 capture group regex with wildcard in the middle

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' '1 2' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 946.96 MB
* Python Subprocess Execution time: 9.54 seconds
* User time (seconds): 8.89
* System time (seconds): 0.63
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:09.53
* Maximum resident set size (MBytes): 3690.88

Result:
```
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
```

# Group 10: pygrep: 2 capture group regex with wildcard in the middle using all

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' 'all' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 952.52 MB
* Python Subprocess Execution time: 8.98 seconds
* User time (seconds): 8.32
* System time (seconds): 0.65
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.97
* Maximum resident set size (MBytes): 3691.12

Result:
```
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
```

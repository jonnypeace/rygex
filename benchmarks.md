Updated: 18-06-2024 21:42:57

############################################################################

# Group 1: pygrep: Regex search DST with digit dot pattern, single threaded

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 789.68 MB
* Python Subprocess Execution time: 13.09 seconds
* User time (seconds): 12.58
* System time (seconds): 0.50
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.08
* Maximum resident set size (MBytes): 3520.50

Result:
```
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
```

# Group 1: pygrep: Regex search DST with digit dot pattern and multithreaded (12) count

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2256.47 MB
* Python Subprocess Execution time: 12.42 seconds
* User time (seconds): 25.55
* System time (seconds): 12.23
* Percent of CPU this job got: 304%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.41
* Maximum resident set size (MBytes): 2162.70

Result:
```
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
```

############################################################################

# Group 2: pygrep: String Search Between SRC= and DST in UFW log using pygrep

```./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 789.82 MB
* Python Subprocess Execution time: 12.09 seconds
* User time (seconds): 11.34
* System time (seconds): 0.73
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

* free -k Total System Memory Increase, Converted to MB: 776.85 MB
* Python Subprocess Execution time: 5.46 seconds
* User time (seconds): 4.83
* System time (seconds): 0.62
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.46
* Maximum resident set size (MBytes): 3520.62

Result:
```
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830
```

# Group 2: rg: search SRC to DST pattern

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -cr '$1'```

* free -k Total System Memory Increase, Converted to MB: 15.44 MB
* Python Subprocess Execution time: 2.75 seconds
* User time (seconds): 2.56
* System time (seconds): 0.18
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.75
* Maximum resident set size (MBytes): 2746.38

Result:
```
11129400
```

# Group 2: rg: search SRC to DST pattern, but with similar output

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 23.11 MB
* Python Subprocess Execution time: 19.31 seconds
* User time (seconds): 17.52
* System time (seconds): 0.27
* Percent of CPU this job got: 96%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:18.37
* Maximum resident set size (MBytes): 2746.75

Result:
```
 556470 157.240.225.34
  61830 62.233.50.245
10511100 79.124.59.134
```

############################################################################

# Group 3: rg: search DST with specific IP

```rg --no-unicode -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 19.74 MB
* Python Subprocess Execution time: 3.43 seconds
* User time (seconds): 3.23
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:03.43
* Maximum resident set size (MBytes): 2746.50

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 26.44 MB
* Python Subprocess Execution time: 24.29 seconds
* User time (seconds): 24.09
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:24.28
* Maximum resident set size (MBytes): 2753.62

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP multithreaded (12)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m12 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1972.69 MB
* Python Subprocess Execution time: 12.11 seconds
* User time (seconds): 40.43
* System time (seconds): 11.56
* Percent of CPU this job got: 429%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.10
* Maximum resident set size (MBytes): 1861.90

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP multithreaded (4)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m4 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2345.20 MB
* Python Subprocess Execution time: 13.31 seconds
* User time (seconds): 36.90
* System time (seconds): 12.09
* Percent of CPU this job got: 368%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.30
* Maximum resident set size (MBytes): 2280.23

Result:
```
124.14.124.14
```

############################################################################

# Group 4: rg: String rg search specific IP

```rg -No -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 8.25 MB
* Python Subprocess Execution time: 0.38 seconds
* User time (seconds): 0.18
* System time (seconds): 0.19
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.50

Result:
```
124.14.124.14
```

# Group 4: pygrep: String Search DST ending with specific IP

```./pygrep.py -s ' DST=' 1 -e '124.14.124.14' 1 -of 5 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 80.07 MB
* Python Subprocess Execution time: 10.80 seconds
* User time (seconds): 10.37
* System time (seconds): 0.42
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:10.80
* Maximum resident set size (MBytes): 13.12

Result:
```
124.14.124.14
```

############################################################################

# Group 5: pygrep: DST with another specific IP

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 781.30 MB
* Python Subprocess Execution time: 26.71 seconds
* User time (seconds): 26.18
* System time (seconds): 0.52
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:26.70
* Maximum resident set size (MBytes): 3520.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: pygrep: DST with another specific IP and multithreaded (12) count

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2581.19 MB
* Python Subprocess Execution time: 13.53 seconds
* User time (seconds): 45.01
* System time (seconds): 11.85
* Percent of CPU this job got: 420%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.53
* Maximum resident set size (MBytes): 2459.60

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: rg: search exact DST match builtin count

```rg --no-unicode -No '\s+DST=(123.12.123.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 38.62 MB
* Python Subprocess Execution time: 6.15 seconds
* User time (seconds): 5.97
* System time (seconds): 0.17
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:06.15
* Maximum resident set size (MBytes): 2746.38

Result:
```
11129399
```

# Group 5: pygrep: DST exact match pattern

```./pygrep.py -p ' DST=(123\.12\.123\.12)' all -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 771.03 MB
* Python Subprocess Execution time: 5.39 seconds
* User time (seconds): 4.86
* System time (seconds): 0.52
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.39
* Maximum resident set size (MBytes): 3520.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: rg: search DST exact match with builtin count

```rg -No ' DST=(123\.12\.123\.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 13.00 MB
* Python Subprocess Execution time: 1.36 seconds
* User time (seconds): 1.16
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.35
* Maximum resident set size (MBytes): 2746.50

Result:
```
11129399
```

############################################################################

# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -p '124\.14\.124\.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 19.43 MB
* Python Subprocess Execution time: 1.11 seconds
* User time (seconds): 0.93
* System time (seconds): 0.17
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.10
* Maximum resident set size (MBytes): 2753.75

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: rg: fixed string search specific IP

```rg -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 7.01 MB
* Python Subprocess Execution time: 0.38 seconds
* User time (seconds): 0.18
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.38

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: grep: fixed string search specific IP

```grep -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 9.14 MB
* Python Subprocess Execution time: 0.83 seconds
* User time (seconds): 0.60
* System time (seconds): 0.22
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.83
* Maximum resident set size (MBytes): 2.38

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -s '124.14.124.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 17.91 MB
* Python Subprocess Execution time: 2.35 seconds
* User time (seconds): 1.94
* System time (seconds): 0.40
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.35
* Maximum resident set size (MBytes): 13.12

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

############################################################################

# Group 7: pygrep: Struggles Here. Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 786.92 MB
* Python Subprocess Execution time: 78.28 seconds
* User time (seconds): 77.77
* System time (seconds): 0.49
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:18.27
* Maximum resident set size (MBytes): 3520.62

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 7: pygrep: Lets try with multithreading (12). Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2868.32 MB
* Python Subprocess Execution time: 20.14 seconds
* User time (seconds): 172.10
* System time (seconds): 13.29
* Percent of CPU this job got: 920%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:20.13
* Maximum resident set size (MBytes): 2748.82

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 7: rg: very good performance by comparison

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 26.71 MB
* Python Subprocess Execution time: 8.81 seconds
* User time (seconds): 8.56
* System time (seconds): 0.24
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.80
* Maximum resident set size (MBytes): 2746.12

Result:
```
11129399
```

# Group 7: rg: same as above, BUT to get the similat output...

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -r '$1' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 32.79 MB
* Python Subprocess Execution time: 49.05 seconds
* User time (seconds): 47.95
* System time (seconds): 0.22
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:48.18
* Maximum resident set size (MBytes): 2746.88

Result:
```
11129399 123.12.123.12
```

############################################################################

# Group 8: rg: Wildcard . Searches

```rg --no-unicode -No '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 32.00 MB
* Python Subprocess Execution time: 13.52 seconds
* User time (seconds): 13.30
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.51
* Maximum resident set size (MBytes): 2746.50

Result:
```
11129399
```

# Group 8: pygrep: Wildcard . Searches

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 777.82 MB
* Python Subprocess Execution time: 52.82 seconds
* User time (seconds): 52.32
* System time (seconds): 0.49
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:52.81
* Maximum resident set size (MBytes): 3520.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 8: pygrep: Wildcard . Searches multithreaded (12)

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 2693.05 MB
* Python Subprocess Execution time: 16.05 seconds
* User time (seconds): 109.02
* System time (seconds): 12.55
* Percent of CPU this job got: 757%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:16.04
* Maximum resident set size (MBytes): 2577.28

Result:
```
123.12.123.12    Line-Counts = 11129399
```

############################################################################

# Group 9: rg: wildcard .* with unicode

```rg --no-unicode -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 35.05 MB
* Python Subprocess Execution time: 11.01 seconds
* User time (seconds): 10.83
* System time (seconds): 0.17
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.01
* Maximum resident set size (MBytes): 2746.25

Result:
```
11129399
```

# Group 9: rg: wildcard .*

```rg -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 23.16 MB
* Python Subprocess Execution time: 11.09 seconds
* User time (seconds): 10.90
* System time (seconds): 0.17
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.08
* Maximum resident set size (MBytes): 2746.38

Result:
```
11129399
```

# Group 9: pygrep: .* Previous result 11.8s

```./pygrep.py -p '.*DST=(123.12.123.12).*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 776.08 MB
* Python Subprocess Execution time: 7.15 seconds
* User time (seconds): 6.53
* System time (seconds): 0.61
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:07.14
* Maximum resident set size (MBytes): 3520.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

############################################################################

# Group 10: rg: 2 capture group regex with wildcard in the middle

```rg -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 19.24 MB
* Python Subprocess Execution time: 8.61 seconds
* User time (seconds): 8.37
* System time (seconds): 0.22
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.60
* Maximum resident set size (MBytes): 2746.50

Result:
```
11129400
```

# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 17.78 MB
* Python Subprocess Execution time: 8.58 seconds
* User time (seconds): 8.39
* System time (seconds): 0.18
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.58
* Maximum resident set size (MBytes): 2746.38

Result:
```
11129400
```

# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle, but unix tool similar output

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -r '$1 $2' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 36.97 MB
* Python Subprocess Execution time: 94.07 seconds
* User time (seconds): 92.67
* System time (seconds): 0.30
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:32.98
* Maximum resident set size (MBytes): 2746.88

Result:
```
 556470 157.240.225.34 443
  61830 62.233.50.245 51914
10511100 79.124.59.134 44991
```

# Group 10: pygrep: 2 capture group regex with wildcard in the middle

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' '1 2' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 952.80 MB
* Python Subprocess Execution time: 9.49 seconds
* User time (seconds): 8.88
* System time (seconds): 0.60
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:09.49
* Maximum resident set size (MBytes): 3690.99

Result:
```
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
```

# Group 10: pygrep: 2 capture group regex with wildcard in the middle using all

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' 'all' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 951.29 MB
* Python Subprocess Execution time: 8.92 seconds
* User time (seconds): 8.32
* System time (seconds): 0.59
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.91
* Maximum resident set size (MBytes): 3691.12

Result:
```
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
```

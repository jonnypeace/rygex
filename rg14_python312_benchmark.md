

ripgrep 14.1.0

features:-simd-accel,+pcre2
simd(compile):+SSE2,-SSSE3,-AVX2
simd(runtime):+SSE2,+SSSE3,+AVX2

PCRE2 10.42 is available (JIT is available)


Python 3.12.4


Updated: 07-07-2024 17:12:18

############################################################################

# Group 1: pygrep: Regex search DST with digit dot pattern, single threaded

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.57 MB
* Python Subprocess Execution time: 18.57 seconds
* User time (seconds): 17.99
* System time (seconds): 0.53
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.50

Result:
```
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
```

# Group 1: pygrep: Regex search DST with digit dot pattern and multithreaded (12) count

```./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1086.46 MB
* Python Subprocess Execution time: 12.07 seconds
* User time (seconds): 28.99
* System time (seconds): 12.96
* Percent of CPU this job got: 347%
* Maximum resident set size (MBytes): 1005.70

Result:
```
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
```

############################################################################

# Group 2: pygrep: String Search Between SRC= and DST in UFW log using pygrep

```./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 778.06 MB
* Python Subprocess Execution time: 11.27 seconds
* User time (seconds): 9.39
* System time (seconds): 1.81
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 778.84

Result:
```
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830
```

# Group 2: pygrep: SRC to DST pattern match

```./pygrep.py -p 'SRC=([\d\.]+)\s+DST' all -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 782.59 MB
* Python Subprocess Execution time: 5.93 seconds
* User time (seconds): 5.29
* System time (seconds): 0.59
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.50

Result:
```
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830
```

# Group 2: rg: search SRC to DST pattern

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -cr '$1'```

* free -k Total System Memory Increase, Converted to MB: 7.07 MB
* Python Subprocess Execution time: 3.13 seconds
* User time (seconds): 2.83
* System time (seconds): 0.22
* Percent of CPU this job got: 97%
* Maximum resident set size (MBytes): 2744.75

Result:
```
11129400
```

# Group 2: rg: search SRC to DST pattern, but with similar output

```rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 15.45 MB
* Python Subprocess Execution time: 8.02 seconds
* User time (seconds): 5.57
* System time (seconds): 0.25
* Percent of CPU this job got: 84%
* Maximum resident set size (MBytes): 2744.75

Result:
```
 556470 157.240.225.34
  61830 62.233.50.245
10511100 79.124.59.134
```

############################################################################

# Group 3: rg: search DST with specific IP

```rg --no-unicode -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 7.07 MB
* Python Subprocess Execution time: 0.37 seconds
* User time (seconds): 0.12
* System time (seconds): 0.22
* Percent of CPU this job got: 96%
* Maximum resident set size (MBytes): 2744.88

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 14.80 MB
* Python Subprocess Execution time: 29.92 seconds
* User time (seconds): 29.44
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 2752.50

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP multithreaded (12)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m12 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 832.92 MB
* Python Subprocess Execution time: 11.61 seconds
* User time (seconds): 46.50
* System time (seconds): 13.49
* Percent of CPU this job got: 516%
* Maximum resident set size (MBytes): 782.37

Result:
```
124.14.124.14
```

# Group 3: pygrep: DST with specific IP multithreaded (4)

```./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m4 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1484.03 MB
* Python Subprocess Execution time: 13.57 seconds
* User time (seconds): 42.17
* System time (seconds): 13.49
* Percent of CPU this job got: 410%
* Maximum resident set size (MBytes): 1454.68

Result:
```
124.14.124.14
```

############################################################################

# Group 4: rg: String rg search specific IP

```rg -No -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 6.70 MB
* Python Subprocess Execution time: 0.37 seconds
* User time (seconds): 0.15
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 2744.75

Result:
```
124.14.124.14
```

# Group 4: pygrep: String Search DST ending with specific IP

```./pygrep.py -s ' DST=' 1 -e '124.14.124.14' 1 -of 5 -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 8.99 MB
* Python Subprocess Execution time: 10.21 seconds
* User time (seconds): 8.90
* System time (seconds): 1.26
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 12.00

Result:
```
124.14.124.14
```

############################################################################

# Group 5: pygrep: DST with another specific IP

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.32 MB
* Python Subprocess Execution time: 31.66 seconds
* User time (seconds): 31.00
* System time (seconds): 0.61
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: pygrep: DST with another specific IP and multithreaded (12) count

```./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 920.12 MB
* Python Subprocess Execution time: 12.49 seconds
* User time (seconds): 49.63
* System time (seconds): 12.17
* Percent of CPU this job got: 495%
* Maximum resident set size (MBytes): 827.68

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: rg: search exact DST match builtin count

```rg --no-unicode -No '\s+DST=(123.12.123.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 6.98 MB
* Python Subprocess Execution time: 8.21 seconds
* User time (seconds): 7.92
* System time (seconds): 0.16
* Percent of CPU this job got: 98%
* Maximum resident set size (MBytes): 2744.75

Result:
```
11129399
```

# Group 5: pygrep: DST exact match pattern

```./pygrep.py -p ' DST=(123\.12\.123\.12)' all -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 782.35 MB
* Python Subprocess Execution time: 5.74 seconds
* User time (seconds): 5.03
* System time (seconds): 0.66
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.62

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 5: rg: search DST exact match with builtin count

```rg -No ' DST=(123\.12\.123\.12)' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 6.92 MB
* Python Subprocess Execution time: 3.03 seconds
* User time (seconds): 2.80
* System time (seconds): 0.15
* Percent of CPU this job got: 98%
* Maximum resident set size (MBytes): 2744.75

Result:
```
11129399
```

############################################################################

# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -p '124\.14\.124\.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 14.56 MB
* Python Subprocess Execution time: 1.80 seconds
* User time (seconds): 1.56
* System time (seconds): 0.19
* Percent of CPU this job got: 97%
* Maximum resident set size (MBytes): 2752.50

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: rg: fixed string search specific IP

```rg -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 6.59 MB
* Python Subprocess Execution time: 0.37 seconds
* User time (seconds): 0.15
* System time (seconds): 0.20
* Percent of CPU this job got: 98%
* Maximum resident set size (MBytes): 2744.62

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: grep: fixed string search specific IP

```grep -F '124.14.124.14' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1.66 MB
* Python Subprocess Execution time: 1.05 seconds
* User time (seconds): 0.67
* System time (seconds): 0.37
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 1.62

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

# Group 6: pygrep: fixed string search specific IP

```./pygrep.py -s '124.14.124.14' -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 8.86 MB
* Python Subprocess Execution time: 3.37 seconds
* User time (seconds): 1.85
* System time (seconds): 1.43
* Percent of CPU this job got: 97%
* Maximum resident set size (MBytes): 11.88

Result:
```
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
```

############################################################################

# Group 7: pygrep: Struggles Here. Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.38 MB
* Python Subprocess Execution time: 95.93 seconds
* User time (seconds): 95.23
* System time (seconds): 0.55
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.38

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 7: pygrep: Lets try with multithreading (12). Previous Result 100Sec

```./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1792.33 MB
* Python Subprocess Execution time: 18.14 seconds
* User time (seconds): 174.34
* System time (seconds): 11.44
* Percent of CPU this job got: 1024%
* Maximum resident set size (MBytes): 1698.25

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 7: rg: very good performance by comparison

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 6.77 MB
* Python Subprocess Execution time: 3.21 seconds
* User time (seconds): 2.99
* System time (seconds): 0.18
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 2744.62

Result:
```
11129399
```

# Group 7: rg: same as above, BUT to get the similat output...

```rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -r '$1' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 15.41 MB
* Python Subprocess Execution time: 8.61 seconds
* User time (seconds): 6.22
* System time (seconds): 0.26
* Percent of CPU this job got: 86%
* Maximum resident set size (MBytes): 2744.62

Result:
```
11129399 123.12.123.12
```

############################################################################

# Group 8: rg: Wildcard . Searches

```rg --no-unicode -No '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 8.54 MB
* Python Subprocess Execution time: 19.83 seconds
* User time (seconds): 19.58
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 2744.62

Result:
```
11129399
```

# Group 8: pygrep: Wildcard . Searches

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.69 MB
* Python Subprocess Execution time: 62.38 seconds
* User time (seconds): 61.20
* System time (seconds): 0.63
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.12

Result:
```
123.12.123.12    Line-Counts = 11129399
```

# Group 8: pygrep: Wildcard . Searches multithreaded (12)

```./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -m12 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 1452.96 MB
* Python Subprocess Execution time: 14.73 seconds
* User time (seconds): 110.28
* System time (seconds): 12.82
* Percent of CPU this job got: 836%
* Maximum resident set size (MBytes): 1373.83

Result:
```
123.12.123.12    Line-Counts = 11129399
```

############################################################################

# Group 9: rg: wildcard .* with unicode

```rg --no-unicode -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 7.97 MB
* Python Subprocess Execution time: 9.91 seconds
* User time (seconds): 9.61
* System time (seconds): 0.19
* Percent of CPU this job got: 98%
* Maximum resident set size (MBytes): 2744.75

Result:
```
11129399
```

# Group 9: rg: wildcard .*

```rg -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 7.92 MB
* Python Subprocess Execution time: 19.42 seconds
* User time (seconds): 19.21
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 2744.65

Result:
```
11129399
```

# Group 9: pygrep: .* Previous result 11.8s

```./pygrep.py -p '.*DST=(123.12.123.12).*' 1 -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 782.41 MB
* Python Subprocess Execution time: 6.39 seconds
* User time (seconds): 5.77
* System time (seconds): 0.58
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.34

Result:
```
123.12.123.12    Line-Counts = 11129399
```

############################################################################

# Group 10: rg: 2 capture group regex with wildcard in the middle

```rg -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 7.45 MB
* Python Subprocess Execution time: 9.78 seconds
* User time (seconds): 9.48
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 2744.91

Result:
```
11129400
```

# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 6.84 MB
* Python Subprocess Execution time: 8.29 seconds
* User time (seconds): 8.04
* System time (seconds): 0.23
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 2744.75

Result:
```
11129400
```

# Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle, but unix tool similar output

```rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -r '$1 $2' ufw.test1 | sort | uniq -c```

* free -k Total System Memory Increase, Converted to MB: 15.57 MB
* Python Subprocess Execution time: 25.11 seconds
* User time (seconds): 22.68
* System time (seconds): 0.23
* Percent of CPU this job got: 96%
* Maximum resident set size (MBytes): 2744.50

Result:
```
 556470 157.240.225.34 443
  61830 62.233.50.245 51914
10511100 79.124.59.134 44991
```

# Group 10: pygrep: 2 capture group regex with wildcard in the middle

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' '1 2' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.27 MB
* Python Subprocess Execution time: 9.80 seconds
* User time (seconds): 9.14
* System time (seconds): 0.64
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.23

Result:
```
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
```

# Group 10: pygrep: 2 capture group regex with wildcard in the middle using all

```./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' 'all' -Sc -f ufw.test1```

* free -k Total System Memory Increase, Converted to MB: 783.09 MB
* Python Subprocess Execution time: 9.14 seconds
* User time (seconds): 8.60
* System time (seconds): 0.51
* Percent of CPU this job got: 99%
* Maximum resident set size (MBytes): 3519.62

Result:
```
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
```

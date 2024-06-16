
############################################################################

 #  <span style="color: red;">Group 1: pygrep: Regex search DST with digit dot pattern, single threaded</span> 

<span style="color: green;">*** ./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 803.60 MB
* Python Subprocess Execution time: 13.20 seconds
* Command being timed: "./pygrep.py -p \sDST=([\d\.]+)\s 1 -Sc -f ufw.test1"
* User time (seconds): 12.64
* System time (seconds): 0.54
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.19
* Maximum resident set size (MBytes): 3520.12

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
</span>

 #  <span style="color: red;">Group 1: pygrep: Regex search DST with digit dot pattern and multithreaded (12) count</span> 

<span style="color: green;">*** ./pygrep.py -p '\sDST=([\d\.]+)\s' '1' -m12 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 2274.71 MB
* Python Subprocess Execution time: 12.70 seconds
* Command being timed: "./pygrep.py -p \sDST=([\d\.]+)\s 1 -m12 -Sc -f ufw.test1"
* User time (seconds): 25.91
* System time (seconds): 11.68
* Percent of CPU this job got: 296%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.70
* Maximum resident set size (MBytes): 2160.54

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
124.14.124.14    Line-Counts = 1
</span>

############################################################################

 #  <span style="color: red;">Group 2: pygrep: String Search Between SRC= and DST in UFW log using pygrep</span> 

<span style="color: green;">*** ./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 789.09 MB
* Python Subprocess Execution time: 12.04 seconds
* Command being timed: "./pygrep.py -s SRC= 1 -e  DST 1 -O -Sc -f ufw.test1"
* User time (seconds): 11.16
* System time (seconds): 0.87
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.04
* Maximum resident set size (MBytes): 780.00

 <span style="color: green;">
Result:
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830
</span>

 #  <span style="color: red;">Group 2: pygrep: SRC to DST pattern match</span> 

<span style="color: green;">*** ./pygrep.py -p 'SRC=([\d\.]+)\s+DST' all -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 782.29 MB
* Python Subprocess Execution time: 5.29 seconds
* Command being timed: "./pygrep.py -p SRC=([\d\.]+)\s+DST all -Sc -f ufw.test1"
* User time (seconds): 4.79
* System time (seconds): 0.49
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.29
* Maximum resident set size (MBytes): 3520.62

 <span style="color: green;">
Result:
79.124.59.134     Line-Counts = 10511100
157.240.225.34    Line-Counts = 556470
62.233.50.245     Line-Counts = 61830
</span>

 #  <span style="color: red;">Group 2: rg: search SRC to DST pattern</span> 

<span style="color: green;">*** rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -cr '$1'</span> 

* free -k Total System Memory Increase, Converted to MB: 17.66 MB
* Python Subprocess Execution time: 2.73 seconds
* Command being timed: "rg --no-unicode -No SRC=([\d\.]+)\s+DST ufw.test1 -cr $1"
* User time (seconds): 2.56
* System time (seconds): 0.16
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.73
* Maximum resident set size (MBytes): 2746.50

 <span style="color: green;">
Result:
11129400
</span>

 #  <span style="color: red;">Group 2: rg: search SRC to DST pattern, but with similar output</span> 

<span style="color: green;">*** rg --no-unicode -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | sort | uniq -c</span> 

* free -k Total System Memory Increase, Converted to MB: 28.16 MB
* Python Subprocess Execution time: 19.09 seconds
* Command being timed: "rg --no-unicode -No SRC=([\d\.]+)\s+DST ufw.test1 -r $1"
* User time (seconds): 17.36
* System time (seconds): 0.24
* Percent of CPU this job got: 96%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:18.21
* Maximum resident set size (MBytes): 2746.50

 <span style="color: green;">
Result:
 556470 157.240.225.34
  61830 62.233.50.245
10511100 79.124.59.134
</span>

############################################################################

 #  <span style="color: red;">Group 3: rg: search DST with specific IP</span> 

<span style="color: green;">*** rg --no-unicode -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 15.45 MB
* Python Subprocess Execution time: 3.46 seconds
* Command being timed: "rg --no-unicode -No \s+DST=(124.14.124.14) -r $1 ufw.test1"
* User time (seconds): 3.22
* System time (seconds): 0.22
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:03.45
* Maximum resident set size (MBytes): 2746.38

 <span style="color: green;">
Result:
124.14.124.14
</span>

 #  <span style="color: red;">Group 3: pygrep: DST with specific IP</span> 

<span style="color: green;">*** ./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 24.53 MB
* Python Subprocess Execution time: 24.17 seconds
* Command being timed: "./pygrep.py -p \s+DST=(124.14.124.14) 1 -f ufw.test1"
* User time (seconds): 24.00
* System time (seconds): 0.15
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:24.16
* Maximum resident set size (MBytes): 2753.62

 <span style="color: green;">
Result:
124.14.124.14
</span>

 #  <span style="color: red;">Group 3: pygrep: DST with specific IP multithreaded (12)</span> 

<span style="color: green;">*** ./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m12 -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 2003.86 MB
* Python Subprocess Execution time: 12.06 seconds
* Command being timed: "./pygrep.py -p \s+DST=(124.14.124.14) 1 -m12 -f ufw.test1"
* User time (seconds): 40.53
* System time (seconds): 11.50
* Percent of CPU this job got: 431%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.05
* Maximum resident set size (MBytes): 1896.30

 <span style="color: green;">
Result:
124.14.124.14
</span>

 #  <span style="color: red;">Group 3: pygrep: DST with specific IP multithreaded (4)</span> 

<span style="color: green;">*** ./pygrep.py -p '\s+DST=(124.14.124.14)' 1 -m4 -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 1852.31 MB
* Python Subprocess Execution time: 12.35 seconds
* Command being timed: "./pygrep.py -p \s+DST=(124.14.124.14) 1 -m4 -f ufw.test1"
* User time (seconds): 38.88
* System time (seconds): 9.30
* Percent of CPU this job got: 390%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:12.34
* Maximum resident set size (MBytes): 1767.76

 <span style="color: green;">
Result:
124.14.124.14
</span>

############################################################################

 #  <span style="color: red;">Group 4: rg: String rg search specific IP</span> 

<span style="color: green;">*** rg -No -F '124.14.124.14' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 7.48 MB
* Python Subprocess Execution time: 0.37 seconds
* Command being timed: "rg -No -F 124.14.124.14 ufw.test1"
* User time (seconds): 0.16
* System time (seconds): 0.20
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.38

 <span style="color: green;">
Result:
124.14.124.14
</span>

 #  <span style="color: red;">Group 4: pygrep: String Search DST ending with specific IP</span> 

<span style="color: green;">*** ./pygrep.py -s ' DST=' 1 -e '124.14.124.14' 1 -of 5 -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 20.89 MB
* Python Subprocess Execution time: 10.73 seconds
* Command being timed: "./pygrep.py -s  DST= 1 -e 124.14.124.14 1 -of 5 -f ufw.test1"
* User time (seconds): 10.27
* System time (seconds): 0.45
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:10.73
* Maximum resident set size (MBytes): 13.00

 <span style="color: green;">
Result:
124.14.124.14
</span>

############################################################################

 #  <span style="color: red;">Group 5: pygrep: DST with another specific IP</span> 

<span style="color: green;">*** ./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 799.83 MB
* Python Subprocess Execution time: 26.94 seconds
* Command being timed: "./pygrep.py -p \s+DST=(123.12.123.12) 1 -Sc -f ufw.test1"
* User time (seconds): 26.43
* System time (seconds): 0.50
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:26.94
* Maximum resident set size (MBytes): 3520.62

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

 #  <span style="color: red;">Group 5: pygrep: DST with another specific IP and multithreaded (12) count</span> 

<span style="color: green;">*** ./pygrep.py -p '\s+DST=(123.12.123.12)' 1 -m12 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 2557.61 MB
* Python Subprocess Execution time: 13.54 seconds
* Command being timed: "./pygrep.py -p \s+DST=(123.12.123.12) 1 -m12 -Sc -f ufw.test1"
* User time (seconds): 44.84
* System time (seconds): 12.67
* Percent of CPU this job got: 424%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.54
* Maximum resident set size (MBytes): 2437.52

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

 #  <span style="color: red;">Group 5: rg: search exact DST match builtin count</span> 

<span style="color: green;">*** rg --no-unicode -No '\s+DST=(123.12.123.12)' -cr '$1' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 33.89 MB
* Python Subprocess Execution time: 6.20 seconds
* Command being timed: "rg --no-unicode -No \s+DST=(123.12.123.12) -cr $1 ufw.test1"
* User time (seconds): 5.99
* System time (seconds): 0.20
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:06.20
* Maximum resident set size (MBytes): 2746.25

 <span style="color: green;">
Result:
11129399
</span>

 #  <span style="color: red;">Group 5: pygrep: DST exact match pattern</span> 

<span style="color: green;">*** ./pygrep.py -p ' DST=(123\.12\.123\.12)' all -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 784.40 MB
* Python Subprocess Execution time: 5.62 seconds
* Command being timed: "./pygrep.py -p  DST=(123\.12\.123\.12) all -Sc -f ufw.test1"
* User time (seconds): 5.06
* System time (seconds): 0.55
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:05.61
* Maximum resident set size (MBytes): 3520.50

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

 #  <span style="color: red;">Group 5: rg: search DST exact match with builtin count</span> 

<span style="color: green;">*** rg -No ' DST=(123\.12\.123\.12)' -cr '$1' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 11.42 MB
* Python Subprocess Execution time: 1.38 seconds
* Command being timed: "rg -No  DST=(123\.12\.123\.12) -cr $1 ufw.test1"
* User time (seconds): 1.17
* System time (seconds): 0.20
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.37
* Maximum resident set size (MBytes): 2746.50

 <span style="color: green;">
Result:
11129399
</span>

############################################################################

 #  <span style="color: red;">Group 6: pygrep: fixed string search specific IP</span> 

<span style="color: green;">*** ./pygrep.py -p '124\.14\.124\.14' -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 13.62 MB
* Python Subprocess Execution time: 1.11 seconds
* Command being timed: "./pygrep.py -p 124\.14\.124\.14 -f ufw.test1"
* User time (seconds): 0.87
* System time (seconds): 0.23
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.10
* Maximum resident set size (MBytes): 2753.62

 <span style="color: green;">
Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
</span>

 #  <span style="color: red;">Group 6: rg: fixed string search specific IP</span> 

<span style="color: green;">*** rg -F '124.14.124.14' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 7.74 MB
* Python Subprocess Execution time: 0.38 seconds
* Command being timed: "rg -F 124.14.124.14 ufw.test1"
* User time (seconds): 0.17
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.37
* Maximum resident set size (MBytes): 2746.38

 <span style="color: green;">
Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
</span>

 #  <span style="color: red;">Group 6: grep: fixed string search specific IP</span> 

<span style="color: green;">*** grep -F '124.14.124.14' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 7.23 MB
* Python Subprocess Execution time: 0.84 seconds
* Command being timed: "grep -F 124.14.124.14 ufw.test1"
* User time (seconds): 0.63
* System time (seconds): 0.19
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.83
* Maximum resident set size (MBytes): 2.38

 <span style="color: green;">
Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
</span>

 #  <span style="color: red;">Group 6: pygrep: fixed string search specific IP</span> 

<span style="color: green;">*** ./pygrep.py -s '124.14.124.14' -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 14.98 MB
* Python Subprocess Execution time: 2.37 seconds
* Command being timed: "./pygrep.py -s 124.14.124.14 -f ufw.test1"
* User time (seconds): 1.94
* System time (seconds): 0.42
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:02.36
* Maximum resident set size (MBytes): 13.00

 <span style="color: green;">
Result:
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=44991 DPT=57422 WINDOW=1024 RES=0x00 SYN URGP=0
</span>

############################################################################

 #  <span style="color: red;">Group 7: pygrep: Struggles Here. Previous Result 100Sec</span> 

<span style="color: green;">*** ./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 779.47 MB
* Python Subprocess Execution time: 80.46 seconds
* Command being timed: "./pygrep.py -p \w+\s+DST=(123.12.123.12)\s+\w+ 1 -Sc -f ufw.test1"
* User time (seconds): 79.88
* System time (seconds): 0.56
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:20.45
* Maximum resident set size (MBytes): 3520.62

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

 #  <span style="color: red;">Group 7: pygrep: Lets try with multithreading (12). Previous Result 100Sec</span> 

<span style="color: green;">*** ./pygrep.py -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -m12 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 2887.04 MB
* Python Subprocess Execution time: 20.60 seconds
* Command being timed: "./pygrep.py -p \w+\s+DST=(123.12.123.12)\s+\w+ 1 -m12 -Sc -f ufw.test1"
* User time (seconds): 173.83
* System time (seconds): 13.35
* Percent of CPU this job got: 908%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:20.59
* Maximum resident set size (MBytes): 2766.13

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

 #  <span style="color: red;">Group 7: rg: very good performance by comparison</span> 

<span style="color: green;">*** rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -cr '$1' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 37.45 MB
* Python Subprocess Execution time: 8.62 seconds
* Command being timed: "rg --no-unicode -No \w+\s+DST=(123.12.123.12)\s+\w+ -cr $1 ufw.test1"
* User time (seconds): 8.42
* System time (seconds): 0.19
* Percent of CPU this job got: 100%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.61
* Maximum resident set size (MBytes): 2746.38

 <span style="color: green;">
Result:
11129399
</span>

 #  <span style="color: red;">Group 7: rg: same as above, BUT to get the similat output...</span> 

<span style="color: green;">*** rg --no-unicode -No '\w+\s+DST=(123.12.123.12)\s+\w+' -r '$1' ufw.test1 | sort | uniq -c</span> 

* free -k Total System Memory Increase, Converted to MB: 29.18 MB
* Python Subprocess Execution time: 49.38 seconds
* Command being timed: "rg --no-unicode -No \w+\s+DST=(123.12.123.12)\s+\w+ -r $1 ufw.test1"
* User time (seconds): 48.24
* System time (seconds): 0.25
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:48.50
* Maximum resident set size (MBytes): 2746.75

 <span style="color: green;">
Result:
11129399 123.12.123.12
</span>

############################################################################

 #  <span style="color: red;">Group 8: rg: Wildcard . Searches</span> 

<span style="color: green;">*** rg --no-unicode -No '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' -cr '$1' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 22.05 MB
* Python Subprocess Execution time: 13.14 seconds
* Command being timed: "rg --no-unicode -No .*\w+\s+DST=(123.12.123.12)\s+\w+.* -cr $1 ufw.test1"
* User time (seconds): 12.96
* System time (seconds): 0.17
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:13.14
* Maximum resident set size (MBytes): 2746.38

 <span style="color: green;">
Result:
11129399
</span>

 #  <span style="color: red;">Group 8: pygrep: Wildcard . Searches</span> 

<span style="color: green;">*** ./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 784.71 MB
* Python Subprocess Execution time: 51.52 seconds
* Command being timed: "./pygrep.py -p .*\w+\s+DST=(123.12.123.12)\s+\w+.* 1 -Sc -f ufw.test1"
* User time (seconds): 50.92
* System time (seconds): 0.59
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:51.51
* Maximum resident set size (MBytes): 3520.34

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

 #  <span style="color: red;">Group 8: pygrep: Wildcard . Searches multithreaded (12)</span> 

<span style="color: green;">*** ./pygrep.py -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -m12 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 2829.95 MB
* Python Subprocess Execution time: 16.45 seconds
* Command being timed: "./pygrep.py -p .*\w+\s+DST=(123.12.123.12)\s+\w+.* 1 -m12 -Sc -f ufw.test1"
* User time (seconds): 108.48
* System time (seconds): 12.88
* Percent of CPU this job got: 738%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:16.44
* Maximum resident set size (MBytes): 2714.48

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

############################################################################

 #  <span style="color: red;">Group 9: rg: wildcard .* with unicode</span> 

<span style="color: green;">*** rg --no-unicode -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 26.52 MB
* Python Subprocess Execution time: 11.61 seconds
* Command being timed: "rg --no-unicode -No .*DST=(123.12.123.12).* -cr $1 ufw.test1"
* User time (seconds): 11.43
* System time (seconds): 0.17
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.61
* Maximum resident set size (MBytes): 2746.38

 <span style="color: green;">
Result:
11129399
</span>

 #  <span style="color: red;">Group 9: rg: wildcard .*</span> 

<span style="color: green;">*** rg -No '.*DST=(123.12.123.12).*' -cr '$1' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 20.97 MB
* Python Subprocess Execution time: 11.48 seconds
* Command being timed: "rg -No .*DST=(123.12.123.12).* -cr $1 ufw.test1"
* User time (seconds): 11.22
* System time (seconds): 0.25
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:11.47
* Maximum resident set size (MBytes): 2746.38

 <span style="color: green;">
Result:
11129399
</span>

 #  <span style="color: red;">Group 9: pygrep: .* Previous result 11.8s</span> 

<span style="color: green;">*** ./pygrep.py -p '.*DST=(123.12.123.12).*' 1 -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 777.66 MB
* Python Subprocess Execution time: 7.16 seconds
* Command being timed: "./pygrep.py -p .*DST=(123.12.123.12).* 1 -Sc -f ufw.test1"
* User time (seconds): 6.63
* System time (seconds): 0.51
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:07.16
* Maximum resident set size (MBytes): 3520.88

 <span style="color: green;">
Result:
123.12.123.12    Line-Counts = 11129399
</span>

############################################################################

 #  <span style="color: red;">Group 10: rg: 2 capture group regex with wildcard in the middle</span> 

<span style="color: green;">*** rg -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 28.22 MB
* Python Subprocess Execution time: 8.91 seconds
* Command being timed: "rg -No SRC=([\d\.]+).*SPT=([\d\.]+) -cr $1 $2 ufw.test1"
* User time (seconds): 8.72
* System time (seconds): 0.17
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.90
* Maximum resident set size (MBytes): 2746.50

 <span style="color: green;">
Result:
11129400
</span>

 #  <span style="color: red;">Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle</span> 

<span style="color: green;">*** rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -cr '$1 $2' ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 19.87 MB
* Python Subprocess Execution time: 8.61 seconds
* Command being timed: "rg --no-unicode -No SRC=([\d\.]+).*SPT=([\d\.]+) -cr $1 $2 ufw.test1"
* User time (seconds): 8.38
* System time (seconds): 0.21
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:08.60
* Maximum resident set size (MBytes): 2746.50

 <span style="color: green;">
Result:
11129400
</span>

 #  <span style="color: red;">Group 10: rg: 2 capture group regex --no-unicode with wildcard in the middle, but unix tool similar output</span> 

<span style="color: green;">*** rg --no-unicode -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -r '$1 $2' ufw.test1 | sort | uniq -c</span> 

* free -k Total System Memory Increase, Converted to MB: 35.80 MB
* Python Subprocess Execution time: 92.43 seconds
* Command being timed: "rg --no-unicode -No SRC=([\d\.]+).*SPT=([\d\.]+) -r $1 $2 ufw.test1"
* User time (seconds): 91.06
* System time (seconds): 0.26
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 1:31.34
* Maximum resident set size (MBytes): 2746.75

 <span style="color: green;">
Result:
 556470 157.240.225.34 443
  61830 62.233.50.245 51914
10511100 79.124.59.134 44991
</span>

 #  <span style="color: red;">Group 10: pygrep: 2 capture group regex with wildcard in the middle</span> 

<span style="color: green;">*** ./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' '1 2' -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 963.68 MB
* Python Subprocess Execution time: 9.64 seconds
* Command being timed: "./pygrep.py -p SRC=([\d\.]+).*SPT=([\d\.]+) 1 2 -Sc -f ufw.test1"
* User time (seconds): 8.99
* System time (seconds): 0.64
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:09.63
* Maximum resident set size (MBytes): 3691.00

 <span style="color: green;">
Result:
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
</span>

 #  <span style="color: red;">Group 10: pygrep: 2 capture group regex with wildcard in the middle using all</span> 

<span style="color: green;">*** ./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' 'all' -Sc -f ufw.test1</span> 

* free -k Total System Memory Increase, Converted to MB: 952.98 MB
* Python Subprocess Execution time: 9.12 seconds
* Command being timed: "./pygrep.py -p SRC=([\d\.]+).*SPT=([\d\.]+) all -Sc -f ufw.test1"
* User time (seconds): 8.52
* System time (seconds): 0.59
* Percent of CPU this job got: 99%
* Elapsed (wall clock) time (h:mm:ss or m:ss): 0:09.11
* Maximum resident set size (MBytes): 3691.00

 <span style="color: green;">
Result:
79.124.59.134 44991    Line-Counts = 10511100
157.240.225.34 443     Line-Counts = 556470
62.233.50.245 51914    Line-Counts = 61830
</span>

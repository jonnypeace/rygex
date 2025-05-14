# RYGEX
## Python (with some rust) string and regex search

## The Why?

Well, I think tools like grep, sed and awk, tail, head are amazing, but thought i’d write something that does a bit of all of them.

This will be under development as i think of new things to add, and optimize the code.

## Info

Tested on Python 3.12+ for the most part on Ubuntu24.04 and Arch Linux, very little testing has taken place on other versions.

After seeking some feedback on rygex, rygex might not be the right tool for every job, but what is? Anyway, I have some performance tests for comparison, and with a new rust library i've implemented for python, the stats have improved.

## Features I'd like to add or improve

* improve docstrings
* debug to the point where I feel I can create a stable branch

## Basic Rules

* Required args are at least --start or --pyreg or --rpyreg (for rust) or --fixed-string otherwise the programme won't do anything
* Requires input from --file or if using piped input from another command (requires -s, or -p for pipes at the minute).
* --pyreg doesn't use --end
* --omitlast requires --end
* --omitfirst requires --start

## What is here?

* rygex_ext: A rust library i've written, which python developers can import and use instead of pythons regex. It's not a drop in replacement, but it is very easy to use.
* rygex: A commmandline regex, string search, filter by lines, match counts, totals, sort, reverse, unique and capable of rust parallel processing.

## String Searches
Basic string searches using -s | --start and -e | --end
* -s | --start: This uses a starting string/word/character on a line, and can take an optional number value (default is to print full line if excluded). The number value will switch to a different index in the line. For example.. if you require the 2nd position of string/word/character in the line, you would simply follow with the number 2. This has been upgraded to use a rust library to help with speed. Note: Requires --end
```./rygex.py --start string 2 -f filename ```

* -e | --end is optional and provides an end to the line you are searching for. Say for instance you only want a string which is enclosed in brackets 
```./rygex.py --start '(' 1 --end ')' 1 -f filename ``` This would select the 1st end character found. For now --end takes 2 arguments. The character/string/word followed by a numerical value would end the string at that index. This has been upgraded to use a rust library to help with speed. Note: Requires --start

* -of | --omitfirst is optional for deleting the first characters of your match. For instance, using the above example, you might want something enclosed in brackets, but without the brackets. ``` ./rygex.py --start cron 1 -of -f /var/log/syslog ``` (default without specifying a number of characters to omit, will remove the characters in --start from the output, otherwise use an integar for the number of characters). This has been upgraded to use a rust library to help with speed.

* -ol | --omitlast is optional and same use as --omitfirst. This would default to number of characters in the --end arg, unless a number value is included. This has been upgraded to use a rust library to help with speed.

* -O | --omitall is optional and combines both -of and -ol. This has been upgraded to use a rust library to help with speed.

* -u | --unique is optional, and will output unique entries only.

* -S | --sort is optional, and will output in sorted order. When used with --counts, it sorts by count value. Now includes an 'r' flag to reverse output, i.e. -Sr.

* -l | --lines is optional and to save piping using tail, head or sed. Examples are easier to understand and syntax easy. You can select a range of lines, i.e. '5:11' last 3 lines '-3:' a single line '5', last line '-1', line 5 to end '5:'. Small gotya, this is programming speak, so remember 0 will be your first line. If you want lines 1-5, then '0:5' will cover you. Another gotya for programming speak, is although '0:5' sounds like you might get 6 lines, 0,1,2,3,4,5: you will only get 0,1,2,3,4, but this is the first 5 lines - bare in mind when using slicing, or if all else fails, use your favourite unix tool like head or tail.
```
./rygex.py --start string -l '-1' -f filename # last line
./rygex.py --start string -l '0:5' -f filename # first 5 lines
```

* -i | --insensitive is optional and whether you want case sensitive searched. No further agrs required.

* -c / --counts is an optional arg which summarises the number of unique lines identified. Works standalone without unique and with --start , --pyreg

* -F / --fixed-string is optional and self explanatory. Same as grep or ripgrep with their -F option. Written in rust.

* -t / --totalcounts is optional, and will give you a total count of all matches. When used with -rp or -F, the implentation is in rust, otherwise python.

* -m / --multi is optional and makes use of multithreading/processing depending if the python or rust implementation is used.

* -rp / --rpyreg Written in rust, usually a lot faster than the python regex engine, probably better for most use cases. May slow down a bit with wildcards like '.*'/ Like -p, optional two args, but need at least the regex string to pass. The second arg is the position of capture groups for printing i.e. '1 2' for capture group 1 and 2.



## Python Regex

I recommend having a read of the python docs for some helpful regular expression used by python. Just enclose the regex in this programme in single quotes to pass the regex to the rygex.py.

https://docs.python.org/3/library/re.html

* -p | --pyreg Up to 2 arguments, one for the regex and the other is for whether you want positional values on the regex using groups - this arg is a number value. Instead of the number value, you could use the keyword 'all', which will show all groups you've enclosed in brackets. The default without any 2nd argument is to print the line.


 ## Examples

 Looks through benchmark data supplied in repo and test scripts for examples, it will save me updating both README and test scripts and benchmark data.
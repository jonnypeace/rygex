#!/usr/bin/env perl
use strict;
use warnings;

# Disable Unicode for performance
binmode(STDIN,  ":raw");
binmode(STDOUT, ":raw");

# Check args
die "Usage: $0 '(regex)' '1 2' file...\n" unless @ARGV >= 3;

my ($pattern, $key_fmt, @files) = @ARGV;
my $re = qr/$pattern/;
my @key_fields = split /\s+/, $key_fmt;

# Shift pattern and key_fmt off @ARGV so <> reads files
shift @ARGV for 1..2;

my %count;

while (<>) {
    if (my @matches = /$re/) {
        # Build key from selected capture groups
        my @vals;
        for my $i (@key_fields) {
            push @vals, $matches[$i - 1];  # -1 since @matches[0] = $1
        }
        my $key = join ' ', @vals;
        $count{$key}++;
    }
}

# Print results sorted by count descending
for my $key (sort { $count{$b} <=> $count{$a} } keys %count) {
    print "$key\t$count{$key}\n";
}


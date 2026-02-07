#!/usr/bin/env perl
use strict;
use warnings;
use File::Temp qw(tempfile);

#—ARGV parsing—
# Usage: count_failures.pl logfile pattern [group_list] [num_threads]
my ($file, $pat, $group_list_str, $workers) = @ARGV;
$workers ||= 4;
die "Usage: $0 logfile pattern [group_list] [num_threads]\n" unless $file && $pat;

# parse group list (e.g., "1,2,3"); default: all capture groups
my @groups = defined $group_list_str && $group_list_str =~ /^\d+(?:,\d+)*$/
    ? split /,/, $group_list_str
    : ();

# compile the regex
my $re = eval { qr/$pat/ };
die "Invalid regex: $@\n" if $@;

# global accumulator
my %global_count;

# prepare temp filenames for each worker
my @tempfiles;
for my $i (0 .. $workers-1) {
    my ($fh, $filename) = tempfile();
    close $fh;  # close parent handle
    push @tempfiles, $filename;
}

# spawn worker processes
for my $worker_id (0 .. $workers-1) {
    my $pid = fork();
    die "Cannot fork: $!\n" unless defined $pid;
    if ($pid == 0) {
        # child: process assigned lines and write to its temp file
        my %local;
        open my $fh_in, '<', $file or die "Cannot open '$file': $!\n";
        my $lineno = 0;
        while (<$fh_in>) {
            if (($lineno++ % $workers) == $worker_id) {
                my @all = ($_ =~ /$re/);
                my @selected = @groups ? map { $all[$_ - 1] } @groups : @all;
                my @defined  = grep defined, @selected;
                $local{ join(',', @defined) }++ if @defined;
            }
        }
        close $fh_in;
                # write local counts to temp file
        my $filename = $tempfiles[$worker_id];
        open my $tf, '>', $filename or die "Cannot open temp file '$filename': $!
";
        for my $key (sort keys %local) {
            print $tf "$key	$local{$key}
";
        }
        close $tf;
        exit 0;
    }
    # parent continues
}

# wait for all children
for (1..$workers) {
    wait;
}

# merge counts from temp files
for my $filename (@tempfiles) {
    open my $tfh, '<', $filename or die "Cannot open temp file '$filename': $!\n";
    while (<$tfh>) {
        chomp;
        my ($key, $count) = split /\t/, $_, 2;
        $global_count{$key} += $count if defined $key && defined $count;
    }
    close $tfh;
    unlink $filename;
}

# output sorted results
for my $key (sort keys %global_count) {
    next unless length $key;
    print "$key\t$global_count{$key}\n";
}

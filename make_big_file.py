#!/usr/bin/env python3

import gzip, sys
import random
from pathlib import Path

# To scale to 10 GiB, set TARGET_BYTES = 10 * 1024**3.
try:
    small = sys.argv[1]
except IndexError:
    small = ''

TARGET_BYTES = 10 * 1024**2  if small == 'small' else 10 * 1024**3

# Define 10 random-ish IP addresses
ip_list = [
    "192.168.1.1",
    "10.0.0.5",
    "172.16.0.12",
    "203.0.113.7",
    "198.51.100.23",
    "8.8.8.8",
    "8.8.4.4",
    "192.0.2.42",
    "54.85.132.14",
    "45.33.32.156"
]

# Define 4 variations of the log message
templates = [
    "Failed password for invalid user {user} from {ip} port 22 ssh2\n",
    "Invalid user {user} from {ip} ssh2: Authentication failure\n",
    "Accepted password for {user} from {ip} port 22 ssh2\n",
    "Connection closed by authenticating user {user} {ip} port 22 [preauth]\n"
]

# Sample set of usernames to randomize
user_list = ["admin", "root", "test", "guest", "ubuntu", "ec2-user", "pi", "oracle", "user1", "developer"]

# Pre-build a chunk of about 1 MiB worth of random log lines
line_samples = []
line_bytes_total = 0
while line_bytes_total < 1 * 1024**2:  # build until ~1 MiB uncompressed
    ip = random.choice(ip_list)
    user = random.choice(user_list)
    tmpl = random.choice(templates)
    line = f"Jan  1 00:00:00 server sshd[12345]: " + tmpl.format(user=user, ip=ip)
    line_bytes = line.encode("utf-8")
    line_samples.append(line_bytes)
    line_bytes_total += len(line_bytes)

# Combine all sample lines into one chunk
chunk = b"".join(line_samples)
chunk_size = len(chunk)

# Compute how many full chunks and leftover lines to reach TARGET_BYTES
full_chunks = TARGET_BYTES // chunk_size
remaining_bytes = TARGET_BYTES - (full_chunks * chunk_size)
out_path = Path("ssh_failures_rand_sample.log.gz")

with gzip.open(out_path, "wb") as f:
    # Write full chunks
    for _ in range(full_chunks):
        f.write(chunk)
    # Write remaining bytes, line by line
    current_bytes = 0
    while current_bytes < remaining_bytes:
        ip = random.choice(ip_list)
        user = random.choice(user_list)
        tmpl = random.choice(templates)
        line = f"Jan  1 00:00:00 server sshd[12345]: " + tmpl.format(user=user, ip=ip)
        line_bytes = line.encode("utf-8")
        if current_bytes + len(line_bytes) > remaining_bytes:
            break
        f.write(line_bytes)
        current_bytes += len(line_bytes)


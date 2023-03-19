#!/bin/bash

while read -r line; do
  if [[ $line =~ cron ]]; then
    printf '%s\n' "$line"
  fi
done < /var/log/syslog

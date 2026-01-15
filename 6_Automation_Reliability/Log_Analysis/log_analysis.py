#!/usr/bin/env python3
import re

logfile = "system.log"
output = "error_report.txt"

with open(logfile) as f:
    logs = f.readlines()

errors = []

for line in logs:
    if re.search("ERROR|FAIL|CRITICAL", line):
        errors.append(line)

with open(output, "w") as f:
    f.writelines(errors)

print(f"Detected {len(errors)} errors.")

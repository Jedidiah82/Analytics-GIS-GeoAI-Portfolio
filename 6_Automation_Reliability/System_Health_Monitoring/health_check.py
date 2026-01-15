#!/usr/bin/env python3
import shutil
import psutil
import socket
import emails

def check_cpu():
    return psutil.cpu_percent() < 80

def check_disk():
    disk = shutil.disk_usage("/")
    return (disk.free / disk.total) * 100 > 20

def check_memory():
    mem = psutil.virtual_memory()
    return mem.available > 100 * 1024 * 1024

def check_dns():
    return socket.gethostbyname("localhost") == "127.0.0.1"

def main():
    issues = []

    if not check_cpu():
        issues.append("CPU usage is over 80%")
    if not check_disk():
        issues.append("Disk space is below 20%")
    if not check_memory():
        issues.append("Available memory is below 100MB")
    if not check_dns():
        issues.append("Hostname resolution failed")

    if issues:
        body = "\n".join(issues)
        message = emails.generate(
            "automation@example.com",
            "student@example.com",
            "System Health Alert",
            body
        )
        emails.send(message)

if __name__ == "__main__":
    main()

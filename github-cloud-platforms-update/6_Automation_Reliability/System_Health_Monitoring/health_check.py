"""One-shot host monitoring; JSON by default and opt-in SMTP."""
import argparse
import json
import os
from pathlib import Path
import shutil
import smtplib
import socket
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
import psutil


def disk_free_percent(path):
    usage = shutil.disk_usage(path)
    return 100 * usage.free / usage.total


def collect(path, interval):
    checks = {}
    probes = {
        "cpu_percent": lambda: psutil.cpu_percent(interval=interval),
        "disk_free_percent": lambda: disk_free_percent(path),
        "available_memory_mb": lambda: psutil.virtual_memory().available / 1024**2,
        "localhost_ipv4": lambda: socket.gethostbyname("localhost"),
    }
    for name, probe in probes.items():
        try:
            checks[name] = {"value": probe()}
        except Exception as exc:
            checks[name] = {"error": type(exc).__name__}
    return checks


def evaluate(checks, cpu=80, disk=20, memory=100):
    issues, errors = [], []
    rules = {
        "cpu_percent": lambda x: x >= cpu,
        "disk_free_percent": lambda x: x <= disk,
        "available_memory_mb": lambda x: x <= memory,
        "localhost_ipv4": lambda x: x != "127.0.0.1",
    }
    for name, rule in rules.items():
        item = checks.get(name, {})
        if "error" in item or "value" not in item:
            errors.append(name)
        elif rule(item["value"]):
            issues.append(name)
    return {"status": "error" if errors else "alert" if issues else "healthy", "issues": issues, "errors": errors, "checks": checks}


def notify(report, environ=None):
    env = os.environ if environ is None else environ
    required = ["MONITOR_SMTP_HOST", "MONITOR_SMTP_USER", "MONITOR_SMTP_PASSWORD", "MONITOR_FROM", "MONITOR_TO"]
    if any(not env.get(k) for k in required):
        raise ValueError("Missing MONITOR_* SMTP configuration")
    message = EmailMessage()
    message["From"], message["To"] = env["MONITOR_FROM"], env["MONITOR_TO"]
    message["Subject"] = "System health: " + report["status"]
    message.set_content(json.dumps(report, indent=2))
    with smtplib.SMTP(env["MONITOR_SMTP_HOST"], int(env.get("MONITOR_SMTP_PORT", "587")), timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(env["MONITOR_SMTP_USER"], env["MONITOR_SMTP_PASSWORD"])
        smtp.send_message(message)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disk-path", default=str(Path.cwd().anchor))
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--cpu", type=float, default=80)
    parser.add_argument("--disk", type=float, default=20)
    parser.add_argument("--memory", type=float, default=100)
    parser.add_argument("--send-email", action="store_true")
    args = parser.parse_args(argv)
    if not (0 < args.interval <= 60 and 0 < args.cpu <= 100 and 0 <= args.disk <= 100 and args.memory >= 0):
        parser.error("Invalid sampling interval or thresholds")
    report = evaluate(collect(args.disk_path, args.interval), args.cpu, args.disk, args.memory)
    report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    report["notification"] = "disabled"
    code = {"healthy": 0, "alert": 1, "error": 2}[report["status"]]
    if args.send_email and code:
        try:
            notify(report)
            report["notification"] = "sent"
        except Exception as exc:
            report["notification"] = "failed: " + type(exc).__name__
            code = 3
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

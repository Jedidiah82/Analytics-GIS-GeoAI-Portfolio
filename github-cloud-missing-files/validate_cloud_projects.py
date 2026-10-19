"""Rerun local checks only; creates no cloud resources and sends no email."""
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parent
PROJECTS = {
 "monitoring": "6_Automation_Reliability/System_Health_Monitoring",
 "aws": "4_Cloud_Computing_Security/aws-ec2-cli-lab",
 "azure": "4_Cloud_Computing_Security/azure-hello-world",
 "cryptography": "4_Cloud_Computing_Security/applied-cryptography-openpgp",
}
def main():
    result = {"timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "python": sys.version.split()[0], "scope": "local unit/artifact checks; cloud and SMTP are not executed", "projects": {}}
    for key, folder in PROJECTS.items():
        directory = BASE/folder
        cmd = [sys.executable, "validate_static.py"] if key == "azure" else [sys.executable, "-m", "unittest", "-v"]
        proc = subprocess.run(cmd, cwd=directory, capture_output=True, text=True, timeout=120)
        output = proc.stdout + proc.stderr
        evidence = directory/"evidence"; evidence.mkdir(exist_ok=True)
        (evidence/"local-tests.txt").write_text(output, encoding="utf-8")
        count = re.search(r"Ran (\d+) tests?", output)
        entry = {"command": "python " + " ".join(cmd[1:]), "exit_code": proc.returncode, "passed": proc.returncode == 0, "tests": int(count[1]) if count else None}
        result["projects"][key] = entry
        (evidence/"validation.json").write_text(json.dumps({"timestamp_utc":result["timestamp_utc"], "scope": result["scope"], **entry}, indent=2))
        print(key, "PASS" if entry["passed"] else "FAIL", entry["tests"])
    (BASE/"CLOUD-VALIDATION.json").write_text(json.dumps(result, indent=2))
    return 0 if all(p["passed"] for p in result["projects"].values()) else 1
if __name__ == "__main__": raise SystemExit(main())

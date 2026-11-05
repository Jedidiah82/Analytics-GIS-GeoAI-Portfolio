"""Run the local test suite and write fresh, machine-readable evidence."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import ssl
import sys
import time
import unittest
import PIL
import cryptography

ROOT = Path(__file__).resolve().parent


def main():
    started=datetime.now(timezone.utc).isoformat();timer=time.monotonic()
    output=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/"tests"))
    result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
    evidence=ROOT/"evidence";evidence.mkdir(exist_ok=True)
    log=output.getvalue();(evidence/"test-results.txt").write_text(log,encoding="utf8")
    data={"schema_version":1,"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),
          "duration_seconds":round(time.monotonic()-timer,3),"success":result.wasSuccessful(),
          "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),
          "python":platform.python_version(),"openssl":ssl.OPENSSL_VERSION,"pillow":PIL.__version__,"cryptography":cryptography.__version__,
          "scope":"Synthetic loopback HTTP/HTTPS tests and CLI subprocesses. No external service, production token or cloud deployment.",
          "tls_test_keys":"Fresh disposable certificates in OS temporary storage; no keys in release files.",
          "source_sha256":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*.py')) if '__pycache__' not in p.parts},
          "limitations":["No penetration test or security certification","No production receiver or durable-storage test","No real credentials or remote uploads","No exactly-once delivery, rollback or automatic POST retry","Timeout is per socket operation, not a total batch deadline"]}
    (evidence/"validation.json").write_text(json.dumps(data,indent=2),encoding="utf8")
    print(log);print("PASS" if result.wasSuccessful() else "FAIL")
    return 0 if result.wasSuccessful() else 1


if __name__=="__main__":sys.exit(main())

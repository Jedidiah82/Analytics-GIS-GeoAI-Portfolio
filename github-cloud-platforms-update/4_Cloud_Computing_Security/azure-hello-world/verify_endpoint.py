"""Check an explicitly supplied public HTTPS deployment after publishing."""
import argparse
from datetime import datetime, timezone
import json
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
import uuid

def verify(base):
    u = urlsplit(base)
    if u.scheme != "https" or u.username or u.password or u.query or u.fragment or u.path not in {"", "/"}: raise ValueError("Provide a public HTTPS origin without credentials, query or path")
    with urlopen(base.rstrip("/") + "/", timeout=30) as response:
        body = response.read(100000).decode("utf-8")
        checks = {"root_200": response.status == 200, "https_final": response.url.startswith("https://"), "expected_page": "Traceable delivery." in body, "nosniff": response.headers.get("X-Content-Type-Options") == "nosniff", "csp": "frame-ancestors 'none'" in response.headers.get("Content-Security-Policy", ""), "referrer_policy": response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin", "permissions_policy": "camera=()" in response.headers.get("Permissions-Policy", "")}
    try:
        with urlopen(base.rstrip("/") + "/missing-" + uuid.uuid4().hex, timeout=30): checks["missing_404"] = False
    except HTTPError as e: checks["missing_404"] = e.code == 404 and "Page not found." in e.read(100000).decode("utf-8")
    return {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "origin": base, "checks": checks, "passed": all(checks.values())}
if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("origin"); a=p.parse_args()
    result = verify(a.origin); print(json.dumps(result, indent=2)); raise SystemExit(0 if result["passed"] else 1)

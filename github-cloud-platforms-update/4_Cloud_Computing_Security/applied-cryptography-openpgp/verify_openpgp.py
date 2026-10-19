"""Exercise GnuPG in a NEW disposable home. Never uses the user's keyring."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess

def exercise(private_dir):
    if private_dir.exists(): raise ValueError("Choose a new private directory; existing homes are never reused")
    private_dir.mkdir(parents=True)
    home = private_dir / "gnupg"
    home.mkdir(mode=0o700)
    gpg = shutil.which("gpg")
    if not gpg: raise RuntimeError("Install official GnuPG/Gpg4win first")
    password = secrets.token_urlsafe(32)
    def run(args, *, secret=False, check=True):
        command = [gpg, "--homedir", str(home.resolve()), "--batch", "--no-tty", "--yes", "--status-fd", "1"]
        if secret: command += ["--pinentry-mode", "loopback", "--passphrase-fd", "0"]
        result = subprocess.run(command + args, input=(password + "\n") if secret else None, capture_output=True, text=True, timeout=90)
        if check and result.returncode: raise RuntimeError("GnuPG stage failed: " + args[0] + " (exit " + str(result.returncode) + ")")
        return result
    message = private_dir / "message.txt"
    message.write_bytes(b"Synthetic public portfolio message. No surveillance or personal data.\n")
    identity = "Portfolio Test <portfolio@example.invalid>"
    run(["--quick-generate-key", identity, "ed25519", "sign", "1d"], secret=True)
    keys = run(["--with-colons", "--list-keys"]).stdout
    fingerprint = next(line.split(":")[9] for line in keys.splitlines() if line.startswith("fpr:"))
    run(["--quick-add-key", fingerprint, "cv25519", "encr", "1d"], secret=True)
    encrypted, recovered, signature = [private_dir / n for n in ["message.gpg", "recovered.txt", "message.sig"]]
    run(["--trust-model", "always", "--recipient", fingerprint, "--output", str(encrypted), "--encrypt", str(message)])
    decrypted = run(["--output", str(recovered), "--decrypt", str(encrypted)], secret=True)
    run(["--local-user", fingerprint, "--output", str(signature), "--detach-sign", str(message)], secret=True)
    verified = run(["--verify", str(signature), str(message)])
    tampered = private_dir / "tampered.txt"; tampered.write_bytes(message.read_bytes() + b"changed\n")
    rejected = run(["--verify", str(signature), str(tampered)], check=False)
    checks = {"plaintext_round_trip": message.read_bytes() == recovered.read_bytes(), "decryption_status": "DECRYPTION_OKAY" in decrypted.stdout, "signature_valid": "VALIDSIG" in verified.stdout, "tamper_rejected": rejected.returncode != 0 and "BADSIG" in rejected.stdout}
    result = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "tool": subprocess.run([gpg, "--version"], capture_output=True, text=True).stdout.splitlines()[0], "data": "synthetic public message", "checks": checks, "message_sha256": hashlib.sha256(message.read_bytes()).hexdigest(), "cloud_key_vault": "not executed", "private_material": "Disposable generated home retained outside publication; passphrase existed only in process memory"}
    if not all(checks.values()): raise RuntimeError("A cryptographic verification failed")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-dir", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    try:
        result = exercise(a.private_dir.resolve())
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "stage_error": str(exc)}))
        return 1
if __name__ == "__main__": raise SystemExit(main())

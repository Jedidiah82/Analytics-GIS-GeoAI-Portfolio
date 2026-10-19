"""Print a plan for an EXISTING Azure Key Vault key. No cloud calls."""
import argparse
import json
import re

def plan(vault, key):
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9-]{1,22}[a-zA-Z0-9]", vault): raise ValueError("Invalid vault name")
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,127}", key): raise ValueError("Invalid key name")
    base = ["--vault-name", vault, "--name", key]
    return {"mode": "plan-only", "cloud_calls": 0, "prerequisites": ["Existing approved vault and RSA key with encrypt/decrypt operations", "Authenticated Entra identity with scoped cryptographic permissions", "Record key version and prove an unauthorized identity is denied separately"], "commands": [["az", "keyvault", "key", "show", *base], ["az", "keyvault", "key", "encrypt", *base, "--algorithm", "RSA-OAEP-256", "--data-type", "plaintext", "--value", "synthetic-portfolio-message"], ["az", "keyvault", "key", "decrypt", *base, "--algorithm", "RSA-OAEP-256", "--data-type", "plaintext", "--value", "REPLACE_WITH_RETURNED_CIPHERTEXT"]], "verification": "Compare recovered plaintext, inspect actual key metadata and access-denial result. No vault creation, role grant or key deletion is automated."}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--vault", required=True); p.add_argument("--key", required=True); a = p.parse_args()
    print(json.dumps(plan(a.vault, a.key), indent=2))

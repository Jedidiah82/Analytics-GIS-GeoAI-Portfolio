"""Metadata CLI. No I/O occurs on import."""
from upload_client import cli

if __name__ == "__main__":
    raise SystemExit(cli("metadata"))

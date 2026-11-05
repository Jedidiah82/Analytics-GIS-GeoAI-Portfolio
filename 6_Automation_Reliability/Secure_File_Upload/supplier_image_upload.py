"""JPEG upload CLI, maintained beside the metadata entry point."""
from upload_client import cli

if __name__ == "__main__":
    raise SystemExit(cli("images"))

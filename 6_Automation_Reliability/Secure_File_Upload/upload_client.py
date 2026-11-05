"""Bounded catalog uploads with explicit transport and acknowledgement contracts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import io
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import secrets
import ssl
import sys
from urllib.parse import urlsplit
import warnings

MAX_METADATA = 65536
MAX_IMAGE = 10 * 1024 * 1024
MAX_RESPONSE = 65536
MAX_BATCH = 100
MAX_BATCH_BYTES = 32 * 1024 * 1024
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.(?:txt|jpeg|jpg)\Z")


class UploadError(Exception):
    """Messages contain stable codes only, never server bodies or credentials."""


def endpoint(url: str, allow_local_http: bool = False):
    if any(ord(c) < 33 or ord(c) == 127 for c in url):
        raise UploadError("invalid_endpoint")
    try:
        parsed = urlsplit(url)
        host, port = parsed.hostname, parsed.port
    except ValueError:
        raise UploadError("invalid_endpoint") from None
    if (parsed.scheme not in {"http", "https"} or not host or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)):
        raise UploadError("invalid_endpoint")
    if parsed.scheme == "http":
        try:
            local = ipaddress.ip_address(host).is_loopback
        except ValueError:
            local = False
        if not allow_local_http or not local:
            raise UploadError("https_required_except_explicit_loopback_test")
    return parsed


def token_from_env() -> str:
    token = os.environ.get("UPLOAD_API_TOKEN", "")
    if not token or len(token) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in token):
        raise UploadError("missing_or_invalid_UPLOAD_API_TOKEN")
    return token


def read_bounded(path: Path, maximum: int) -> bytes:
    if path.is_symlink() or not path.is_file() or not NAME.fullmatch(path.name):
        raise UploadError("invalid_input_file")
    # Open only once: validate and upload these same bytes, rather than reread later.
    with path.open("rb") as source:
        data = source.read(maximum + 1)
    if not data or len(data) > maximum:
        raise UploadError("empty_or_oversized_input")
    return data


def metadata(path: Path):
    try:
        lines = read_bounded(path, MAX_METADATA).decode("utf-8").splitlines()
    except UnicodeError:
        raise UploadError("metadata_must_be_utf8") from None
    if len(lines) < 3:
        raise UploadError("metadata_requires_name_weight_description")
    name, weight = lines[0].strip(), lines[1].strip()
    description = "\n".join(lines[2:]).strip()
    match = re.fullmatch(r"([1-9][0-9]{0,6})(?:\s+lbs)?", weight, re.IGNORECASE)
    if (not name or len(name) > 200 or not description or len(description) > 10000
            or not match or int(match[1]) > 1000000
            or any(ord(c) < 32 and c not in "\n\t" for c in name + description)):
        raise UploadError("invalid_metadata_fields")
    record = {"name": name, "weight": int(match[1]), "description": description,
              "image_name": path.stem + ".jpeg"}
    body = json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    return body, "application/json"


def image(path: Path):
    from PIL import Image, UnidentifiedImageError
    data = read_bounded(path, MAX_IMAGE)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as decoded:
                if decoded.format != "JPEG" or decoded.width * decoded.height > 20000000:
                    raise UploadError("only_bounded_jpeg_images_supported")
                decoded.verify()
            # Full decoding catches truncated pixel data that a header-only probe can miss.
            with Image.open(io.BytesIO(data)) as decoded:
                decoded.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        raise UploadError("invalid_jpeg") from None
    boundary = "catalog-" + secrets.token_hex(16)
    prefix = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
              f'filename="{path.stem}.jpeg"\r\nContent-Type: image/jpeg\r\n\r\n').encode("ascii")
    return prefix + data + f"\r\n--{boundary}--\r\n".encode("ascii"), "multipart/form-data; boundary=" + boundary


def prepare(directory: Path, kind: str):
    if directory.is_symlink() or not directory.is_dir():
        raise UploadError("input_must_be_directory")
    suffixes = {".txt"} if kind == "metadata" else {".jpg", ".jpeg"}
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in suffixes)
    if not paths or len(paths) > MAX_BATCH:
        raise UploadError("batch_requires_1_to_100_files")
    prepared = []
    total = 0
    for path in paths:
        body, content_type = metadata(path) if kind == "metadata" else image(path)
        total += len(body)
        if total > MAX_BATCH_BYTES:
            raise UploadError("prepared_batch_exceeds_32_mib")
        prepared.append((path.name, body, content_type))
    return prepared


def send(parsed, token, body, content_type, timeout, ca_file=None):
    if not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise UploadError("timeout_must_be_between_0_and_120_seconds")
    connection = None
    try:
        if parsed.scheme == "https":
            context = ssl.create_default_context(cafile=ca_file)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            connection = http.client.HTTPSConnection(parsed.hostname, parsed.port, timeout=timeout, context=context)
        else:
            connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=timeout)
        connection.request("POST", parsed.path or "/", body=body, headers={
            "Authorization": "Bearer " + token, "Content-Type": content_type,
            "Accept": "application/json", "User-Agent": "portfolio-catalog-upload/1.0"})
        response = connection.getresponse()
        # http.client never follows redirects: credentials stay on the configured endpoint.
        if not 200 <= response.status < 300:
            raise UploadError("http_status_" + str(response.status))
        if response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            raise UploadError("expected_json_acknowledgement")
        raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise UploadError("oversized_acknowledgement")
        try:
            ack = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError):
            raise UploadError("invalid_json_acknowledgement") from None
        if not isinstance(ack, dict) or not ack:
            raise UploadError("acknowledgement_must_be_nonempty_object")
        return response.status
    except ssl.SSLError:
        raise UploadError("tls_verification_or_handshake_failed") from None
    except (OSError, http.client.HTTPException):
        raise UploadError("transport_failed_outcome_may_be_unknown") from None
    finally:
        if connection is not None:
            connection.close()


def cli(kind: str, argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validated catalog " + kind + " upload")
    parser.add_argument("--endpoint", required=True, help="Configured HTTPS collection URL")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--timeout", default=10.0, type=float, help="Per blocking socket operation, not a total batch deadline")
    parser.add_argument("--ca-file", help="Optional trusted CA PEM; certificate and hostname checks stay enabled")
    parser.add_argument("--allow-local-http", action="store_true", help="Test only: permit literal loopback IP addresses")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without reading a token or connecting")
    args = parser.parse_args(argv)
    report = {"schema_version": 1, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "kind": kind, "dry_run": args.dry_run, "status": "failed", "planned": 0,
              "acknowledged": 0, "files": []}
    try:
        parsed = endpoint(args.endpoint, args.allow_local_http)
        if not math.isfinite(args.timeout) or not 0 < args.timeout <= 120:
            raise UploadError("timeout_must_be_between_0_and_120_seconds")
        batch = prepare(args.input_dir, kind)
        report["planned"] = len(batch)
        token = None if args.dry_run else token_from_env()
        for name, body, content_type in batch:
            item = {"file": name, "request_sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
            if not args.dry_run:
                item["http_status"] = send(parsed, token, body, content_type, args.timeout, args.ca_file)
                report["acknowledged"] += 1
            report["files"].append(item)
        report["status"] = "validated_only" if args.dry_run else "acknowledged"
        code = 0
    except UploadError as error:
        report["error"] = str(error);code = 1
    except (OSError, ValueError):
        report["error"] = "local_input_or_configuration_error";code = 1
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(cli("metadata"))

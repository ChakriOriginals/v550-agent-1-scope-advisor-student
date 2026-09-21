#!/usr/bin/env python3
"""Credential-safe local client for the four V550 Scope Advisor operations.

The student key and deployment endpoint are read from environment variables so
they never appear in process arguments. The JSON body is read from standard
input, and the client injects the sole public credential immediately before the
TLS-verified request.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Mapping, TextIO
from urllib.parse import urlparse


OPERATIONS = ("startSession", "logEvent", "closeSession", "issueReport")
MAX_REQUEST_BYTES = 16_384
MAX_RESPONSE_BYTES = 1_048_576
STUDENT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{11,63}$")
DEPLOYMENT_PATH_RE = re.compile(
    r"^/(?:a/macros/[A-Za-z0-9._-]+|macros)/s/[A-Za-z0-9_-]+/exec/?$"
)


class ClientError(ValueError):
    """A safe, student-displayable configuration or response error."""


def validate_endpoint(value: str) -> str:
    endpoint = value.strip()
    parsed = urlparse(endpoint)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "script.google.com"
        or parsed.username
        or parsed.password
        or parsed.port
        or parsed.query
        or parsed.fragment
        or not DEPLOYMENT_PATH_RE.fullmatch(parsed.path)
    ):
        raise ClientError(
            "V550_ACTION_ENDPOINT must be an HTTPS script.google.com web-app deployment URL."
        )
    return endpoint.rstrip("/")


def validate_student_key(value: str) -> str:
    student_key = value.strip()
    if not STUDENT_KEY_RE.fullmatch(student_key):
        raise ClientError("V550_STUDENT_KEY is missing or has an invalid format.")
    return student_key


def load_request(stream: TextIO) -> dict[str, Any]:
    raw = stream.read(MAX_REQUEST_BYTES + 1)
    if not raw.strip():
        raise ClientError("A JSON object is required on standard input.")
    if len(raw.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ClientError("The request exceeds the 16,384-byte limit.")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ClientError("Standard input must contain valid JSON.") from error
    if not isinstance(value, dict):
        raise ClientError("Standard input must contain one JSON object.")
    return value


def prepare_request(
    operation: str,
    payload: Mapping[str, Any],
    student_key: str,
) -> dict[str, Any]:
    if operation not in OPERATIONS:
        raise ClientError("The requested operation is not allowed.")
    if "studentKey" in payload:
        raise ClientError("Do not place studentKey in request JSON; the client injects it securely.")
    if "classToken" in payload:
        raise ClientError("classToken is prohibited and is not a client credential.")
    if payload.get("operation") not in (None, operation):
        raise ClientError("The request operation does not match the selected operation.")
    prepared = dict(payload)
    prepared["operation"] = operation
    prepared["studentKey"] = student_key
    encoded = json.dumps(prepared, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ClientError("The completed request exceeds the 16,384-byte limit.")
    return prepared


def post_json(endpoint: str, payload: Mapping[str, Any], timeout: float) -> dict[str, Any]:
    curl = shutil.which("curl")
    if not curl:
        raise ClientError("curl is required for certificate-verified telemetry delivery.")
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    completed = subprocess.run(
        [
            curl,
            "--silent",
            "--show-error",
            "--location",
            "--max-time",
            str(timeout),
            "--max-filesize",
            str(MAX_RESPONSE_BYTES),
            "--header",
            "Content-Type: application/json",
            "--data-binary",
            "@-",
            endpoint,
        ],
        input=body,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ClientError(
            "The telemetry endpoint could not be reached securely "
            f"(curl exit {completed.returncode})."
        )
    if len(completed.stdout.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ClientError("The telemetry endpoint returned an oversized response.")
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ClientError("The telemetry endpoint did not return JSON.") from error
    if not isinstance(response, dict):
        raise ClientError("The telemetry endpoint response must be a JSON object.")
    student_key = str(payload.get("studentKey", ""))
    if student_key and student_key in completed.stdout:
        raise ClientError("The telemetry endpoint returned a prohibited credential echo.")
    return response


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=OPERATIONS)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate local configuration without sending a request or printing secrets.",
    )
    args = parser.parse_args(argv)
    if not args.check_config and not args.operation:
        parser.error("operation is required unless --check-config is used")
    if args.timeout <= 0 or args.timeout > 120:
        parser.error("--timeout must be greater than 0 and no more than 120 seconds")
    return args


def main(
    argv: list[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = parse_args(argv)
    environment = os.environ if environ is None else environ
    try:
        endpoint = validate_endpoint(environment.get("V550_ACTION_ENDPOINT", ""))
        student_key = validate_student_key(environment.get("V550_STUDENT_KEY", ""))
        if args.check_config:
            print(
                json.dumps(
                    {
                        "configured": True,
                        "endpointHost": "script.google.com",
                        "studentKeyPresent": True,
                    },
                    sort_keys=True,
                ),
                file=stdout,
            )
            return 0
        payload = load_request(stdin)
        prepared = prepare_request(args.operation, payload, student_key)
        response = post_json(endpoint, prepared, args.timeout)
        print(json.dumps(response, ensure_ascii=False, sort_keys=True), file=stdout)
        return 1 if isinstance(response.get("error"), dict) else 0
    except ClientError as error:
        print(json.dumps({"ok": False, "clientError": str(error)}, sort_keys=True), file=stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

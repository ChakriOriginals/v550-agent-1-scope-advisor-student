#!/usr/bin/env python3
"""Verify file integrity and structure for a local V550 review bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


REQUIRED = {
    "V550_REVIEW_RECORD.json",
    "V550_REVIEW_SHEET.html",
    "V550_REVIEW_MANIFEST.json",
    "README.txt",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as handle:
        names = handle.namelist()
        if set(names) != REQUIRED:
            raise ValueError("The ZIP must contain exactly the four standardized review files.")
        for name in names:
            member = Path(name)
            if member.is_absolute() or ".." in member.parts or len(member.parts) != 1:
                raise ValueError("The ZIP contains an unsafe path.")
        handle.extractall(destination)
    return destination


def verify(directory: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings = [
        "Local hashes detect accidental or uncoordinated edits but do not prove authorship without an instructor-controlled signature."
    ]
    actual_names = {item.name for item in directory.iterdir() if item.is_file()}
    missing = REQUIRED - actual_names
    unexpected = actual_names - REQUIRED
    if missing:
        errors.append("Missing required files: " + ", ".join(sorted(missing)))
    if unexpected:
        errors.append("Unexpected files: " + ", ".join(sorted(unexpected)))
    if missing or unexpected:
        return {"valid": False, "errors": errors, "warnings": warnings}
    try:
        manifest = json.loads((directory / "V550_REVIEW_MANIFEST.json").read_text(encoding="utf-8"))
        record = json.loads((directory / "V550_REVIEW_RECORD.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"Cannot read review JSON: {exc}"], "warnings": warnings}

    if manifest.get("schema_version") != "1.0.0" or record.get("schema_version") != "1.0.0":
        errors.append("Unsupported review-bundle schema version.")
    if manifest.get("document_type") != "V550_LOCAL_REVIEW_BUNDLE" or record.get("document_type") != "V550_LOCAL_REVIEW_BUNDLE":
        errors.append("Unexpected document type.")
    if manifest.get("integrity_scope") != "LOCAL_HASH_ONLY" or record.get("integrity_scope") != "LOCAL_HASH_ONLY":
        errors.append("The required local-integrity disclosure is missing.")

    canonical_generator = Path(__file__).with_name("generate_review_bundle.py")
    if not canonical_generator.is_file():
        errors.append("The canonical review generator is unavailable to this verifier.")
    elif manifest.get("generator_sha256") != sha256_file(canonical_generator):
        errors.append("Generator hash does not match this trusted package version.")

    declared = manifest.get("files")
    if not isinstance(declared, dict):
        errors.append("Manifest file inventory is missing.")
    else:
        expected_declared = REQUIRED - {"V550_REVIEW_MANIFEST.json"}
        if set(declared) != expected_declared:
            errors.append("Manifest file inventory is not the standardized three-file set.")
        for name in expected_declared:
            entry = declared.get(name)
            if not isinstance(entry, dict):
                errors.append(f"Manifest entry missing for {name}.")
                continue
            path = directory / name
            if entry.get("sha256") != sha256_file(path):
                errors.append(f"Hash mismatch: {name}.")
            if entry.get("bytes") != path.stat().st_size:
                errors.append(f"Byte-length mismatch: {name}.")

    transcript = record.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        errors.append("Canonical transcript is empty or malformed.")
    else:
        for expected, message in enumerate(transcript, start=1):
            if not isinstance(message, dict) or message.get("sequence") != expected:
                errors.append("Transcript sequence is not contiguous.")
                break
            if message.get("role") not in {"user", "assistant"} or not isinstance(message.get("text"), str):
                errors.append("Transcript contains an invalid visible-message record.")
                break
        canonical = (json.dumps(transcript, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != record.get("transcript_sha256"):
            errors.append("Transcript hash does not match the canonical record.")
        if record.get("transcript_sha256") != manifest.get("transcript_sha256"):
            errors.append("Transcript hash differs between record and manifest.")

    review = record.get("final_learning_review")
    if not isinstance(review, str) or "v550 final learning review" not in review.casefold():
        errors.append("The standardized final learning review is missing.")
    gates = record.get("gate_outcomes")
    if not isinstance(gates, list) or len(gates) != 6:
        errors.append("The review must contain all six gate outcome rows.")
    elif any(item.get("latest_status") not in {"OPEN", "CLOSED", "NOT REVIEWED"} for item in gates if isinstance(item, dict)):
        errors.append("A gate outcome has an invalid status.")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Review bundle directory or ZIP")
    args = parser.parse_args()
    try:
        target = args.bundle.resolve()
        if target.is_dir():
            result = verify(target)
        elif target.is_file() and target.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory() as temporary:
                result = verify(safe_extract(target, Path(temporary)))
        else:
            raise ValueError("Bundle must be a directory or ZIP file.")
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        result = {"valid": False, "errors": [str(exc)], "warnings": []}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

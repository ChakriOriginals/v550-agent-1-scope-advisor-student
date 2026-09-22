#!/usr/bin/env python3
"""Create a standardized local V550 review bundle from a Codex session."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import stat
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0.0"
DOCUMENT_TYPE = "V550_LOCAL_REVIEW_BUNDLE"
FINAL_REVIEW_MARKER = "V550 Final Learning Review"
ALLOWED_ROLES = {"user", "assistant"}
GATE_NAMES = {
    1: "Big 5 Pre-Planning",
    2: "Requirements",
    3: "Expectations",
    4: "Goals & Objectives",
    5: "Scope of Work",
    6: "Work Breakdown Structure",
}


class ReviewBundleError(ValueError):
    """The local session cannot be converted safely."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def first_session_meta(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                if item.get("type") == "session_meta" and isinstance(item.get("payload"), dict):
                    return item["payload"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return None


def discover_session(session_root: Path, workspace: Path) -> Path:
    if not session_root.is_dir():
        raise ReviewBundleError(f"Codex session directory was not found: {session_root}")
    workspace_resolved = workspace.resolve()
    candidates = sorted(
        session_root.rglob("rollout-*.jsonl"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates[:200]:
        metadata = first_session_meta(candidate)
        cwd = metadata.get("cwd") if metadata else None
        if isinstance(cwd, str):
            try:
                if Path(cwd).resolve() == workspace_resolved:
                    return candidate
            except OSError:
                continue
    raise ReviewBundleError(
        "No Codex session was found for this folder. Open the repository as a local "
        "Codex folder and run the review command from that chat."
    )


def visible_text(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    fragments: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            fragments.append(text.strip())
        elif isinstance(item.get("type"), str):
            fragments.append(f"[Non-text chat item: {item['type']}]")
    return "\n\n".join(fragments).strip()


def load_visible_session(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReviewBundleError(f"Cannot read the Codex session: {exc}") from exc
    if size > 100 * 1024 * 1024:
        raise ReviewBundleError("The Codex session exceeds the 100 MB local export limit.")

    metadata: dict[str, Any] | None = None
    messages: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ReviewBundleError(f"Session record {line_number} is not valid JSON.") from exc
                if item.get("type") == "session_meta" and isinstance(item.get("payload"), dict):
                    metadata = item["payload"]
                    continue
                if item.get("type") != "response_item":
                    continue
                payload = item.get("payload")
                if not isinstance(payload, dict) or payload.get("type") != "message":
                    continue
                role = payload.get("role")
                if role not in ALLOWED_ROLES:
                    continue
                text = visible_text(payload.get("content"))
                if not text:
                    continue
                messages.append(
                    {
                        "sequence": len(messages) + 1,
                        "timestamp": item.get("timestamp"),
                        "role": role,
                        "phase": payload.get("phase") if isinstance(payload.get("phase"), str) else None,
                        "text": text,
                    }
                )
    except (OSError, UnicodeDecodeError) as exc:
        raise ReviewBundleError(f"Cannot read the Codex session: {exc}") from exc

    if metadata is None:
        raise ReviewBundleError("The Codex session has no session metadata.")
    if not any(item["role"] == "user" for item in messages):
        raise ReviewBundleError("The session contains no visible student messages.")
    if not any(item["role"] == "assistant" for item in messages):
        raise ReviewBundleError("The session contains no visible advisor messages.")
    return metadata, messages


def extract_gate_outcomes(messages: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    outcomes: dict[int, dict[str, Any]] = {}
    pattern = re.compile(
        r"(?ms)^Gate:\s*(?:Gate\s*)?([1-6])(?:\s*[.\-:]\s*|\s+)([^\n]+?)\s*$"
        r".*?^Ready to move on:\s*(YES\s*[—-]\s*Gate OPEN|NOT YET\s*[—-]\s*Gate CLOSED)",
        re.IGNORECASE,
    )
    for message in messages:
        if message["role"] != "assistant":
            continue
        for match in pattern.finditer(message["text"]):
            gate = int(match.group(1))
            status = "OPEN" if match.group(3).upper().startswith("YES") else "CLOSED"
            outcomes[gate] = {
                "gate_number": gate,
                "gate_name": GATE_NAMES[gate],
                "latest_status": status,
                "message_sequence": message["sequence"],
            }
    return [
        outcomes.get(
            gate,
            {
                "gate_number": gate,
                "gate_name": name,
                "latest_status": "NOT REVIEWED",
                "message_sequence": None,
            },
        )
        for gate, name in GATE_NAMES.items()
    ]


def final_learning_review(messages: Iterable[dict[str, Any]]) -> str:
    reviews = [
        item["text"]
        for item in messages
        if item["role"] == "assistant" and FINAL_REVIEW_MARKER.casefold() in item["text"].casefold()
    ]
    if not reviews:
        raise ReviewBundleError(
            "The advisor has not produced the standardized final learning review. "
            "Ask the advisor to end the learning session first, then request the review bundle in a new turn."
        )
    return reviews[-1]


def git_commit(workspace: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None


def html_page(record: dict[str, Any], record_hash: str) -> bytes:
    def escaped(value: Any) -> str:
        return html.escape("" if value is None else str(value))

    gate_rows = "\n".join(
        "<tr><td>{}</td><td>{}</td><td><strong>{}</strong></td></tr>".format(
            gate["gate_number"], escaped(gate["gate_name"]), escaped(gate["latest_status"])
        )
        for gate in record["gate_outcomes"]
    )
    transcript = "\n".join(
        "<article class='message {}'><header>Turn {} · {}{}</header><pre>{}</pre></article>".format(
            escaped(message["role"]),
            message["sequence"],
            "Student" if message["role"] == "user" else "Advisor",
            f" · {escaped(message['timestamp'])}" if message.get("timestamp") else "",
            escaped(message["text"]),
        )
        for message in record["transcript"]
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V550 Scope Advisor Review Sheet</title>
<style>
body{{font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:960px;margin:32px auto;padding:0 24px;color:#172033}}
h1,h2{{color:#243b6b}} .notice{{padding:12px 16px;background:#fff6d9;border-left:4px solid #d59a00}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:8px;border:1px solid #ccd3df;text-align:left}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.5 inherit;margin:8px 0 0}}
.message{{margin:14px 0;padding:12px 16px;border-radius:8px;border:1px solid #d8deea}}
.message.user{{background:#f2f6ff}} .message.assistant{{background:#f7f8fa}} header{{font-weight:700;color:#3a4b68}}
.hash{{font:12px/1.4 ui-monospace,SFMono-Regular,monospace;overflow-wrap:anywhere}}
@media print{{body{{margin:0;max-width:none}} .message{{break-inside:avoid}}}}
</style></head><body>
<h1>V550 Scope Advisor Review Sheet</h1>
<p class="notice"><strong>Local review snapshot.</strong> This file is standardized, read-only, and hash-verified, but it is not digitally signed and cannot prove authorship on a student-owned computer.</p>
<h2>Session</h2>
<table><tr><th>Course / term</th><td>V550 / Fall 2026</td></tr>
<tr><th>Local session ID</th><td>{escaped(record['session']['session_id'])}</td></tr>
<tr><th>Workspace</th><td>{escaped(record['session']['workspace_name'])}</td></tr>
<tr><th>Generated</th><td>{escaped(record['generated_at_utc'])}</td></tr>
<tr><th>Visible messages</th><td>{len(record['transcript'])}</td></tr>
<tr><th>Canonical record SHA-256</th><td class="hash">{record_hash}</td></tr></table>
<h2>Gate outcomes</h2><table><thead><tr><th>Gate</th><th>Name</th><th>Latest formal status</th></tr></thead><tbody>{gate_rows}</tbody></table>
<h2>Final learning review</h2><pre>{escaped(record['final_learning_review'])}</pre>
<h2>Complete visible student/advisor transcript</h2>
<p>System instructions, developer instructions, hidden reasoning, tool calls, and tool output are excluded. Attached non-text items are identified by type.</p>
{transcript}
</body></html>"""
    return document.encode("utf-8")


def readonly(path: Path) -> None:
    try:
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        pass


def create_bundle(session_file: Path, workspace: Path, output_root: Path) -> dict[str, Any]:
    metadata, messages = load_visible_session(session_file)
    review = final_learning_review(messages)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    session_id = str(metadata.get("id") or metadata.get("session_id") or "unknown-session")
    safe_session = re.sub(r"[^A-Za-z0-9_-]", "", session_id)[:24] or "session"
    bundle_name = f"v550-review-{generated_at[:10]}-{safe_session}"
    bundle_dir = output_root / bundle_name
    if bundle_dir.exists():
        raise ReviewBundleError(f"Review bundle already exists and will not be overwritten: {bundle_dir}")
    bundle_dir.mkdir(parents=True, exist_ok=False)

    transcript_hash = sha256_bytes(canonical_json(messages))
    record = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPE,
        "generated_at_utc": generated_at,
        "integrity_scope": "LOCAL_HASH_ONLY",
        "session": {
            "session_id": session_id,
            "started_at": metadata.get("timestamp"),
            "originator": metadata.get("originator"),
            "workspace_name": workspace.name,
            "repository_commit": git_commit(workspace),
        },
        "gate_outcomes": extract_gate_outcomes(messages),
        "final_learning_review": review,
        "transcript_sha256": transcript_hash,
        "transcript": messages,
    }
    record_bytes = json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
    record_hash = sha256_bytes(record_bytes)
    html_bytes = html_page(record, record_hash)
    readme_bytes = (
        "V550 LOCAL REVIEW BUNDLE\n\n"
        "Submit the ZIP or all files together. V550_REVIEW_SHEET.html is the human-readable review.\n"
        "V550_REVIEW_RECORD.json is the canonical visible transcript and evaluation record.\n"
        "V550_REVIEW_MANIFEST.json contains integrity hashes.\n\n"
        "The files are marked read-only and hash-checked. Because they were generated on a student-owned\n"
        "computer without an instructor-held signing key, they are tamper-evident only and do not provide\n"
        "cryptographic proof of authorship.\n"
    ).encode("utf-8")

    files = {
        "V550_REVIEW_RECORD.json": record_bytes,
        "V550_REVIEW_SHEET.html": html_bytes,
        "README.txt": readme_bytes,
    }
    generator_hash = sha256_bytes(Path(__file__).read_bytes())
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPE,
        "created_at_utc": generated_at,
        "integrity_scope": "LOCAL_HASH_ONLY",
        "generator_sha256": generator_hash,
        "source_session_file": session_file.name,
        "source_session_sha256": sha256_bytes(session_file.read_bytes()),
        "transcript_sha256": transcript_hash,
        "files": {name: {"sha256": sha256_bytes(data), "bytes": len(data)} for name, data in files.items()},
    }
    files["V550_REVIEW_MANIFEST.json"] = (
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
    )

    for name, data in files.items():
        destination = bundle_dir / name
        destination.write_bytes(data)
        readonly(destination)

    archive = output_root / f"{bundle_name}.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as handle:
        for name in sorted(files):
            handle.write(bundle_dir / name, arcname=name)
    readonly(archive)
    try:
        bundle_dir.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    except OSError:
        pass
    return {
        "valid": True,
        "bundleDirectory": str(bundle_dir),
        "archive": str(archive),
        "visibleMessageCount": len(messages),
        "recordSha256": record_hash,
        "integrityScope": "LOCAL_HASH_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--session-root", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--session-file", type=Path, help="Explicit Codex JSONL session file")
    parser.add_argument("--output-root", type=Path, help="Output directory; defaults inside the workspace")
    args = parser.parse_args()
    try:
        workspace = args.workspace.resolve()
        session_file = args.session_file.resolve() if args.session_file else discover_session(args.session_root, workspace)
        output_root = (args.output_root or workspace / "V550 Review Bundles").resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        result = create_bundle(session_file, workspace, output_root)
    except (ReviewBundleError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

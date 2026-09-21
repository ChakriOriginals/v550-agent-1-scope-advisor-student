#!/usr/bin/env python3
"""Fail closed if the V550 student package crosses its release boundary."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    ROOT / "README.md",
    ROOT / "SECURITY.md",
    ROOT / "install.py",
    ROOT / "start-v550.sh",
    ROOT / "start-v550-desktop.sh",
    ROOT / "config" / "endpoint.txt",
    ROOT / "skills" / "v550-scope-advisor" / "SKILL.md",
    ROOT
    / "skills"
    / "v550-scope-advisor"
    / "scripts"
    / "local_telemetry_client.py",
)
FORBIDDEN_PARTS = {
    "source-material",
    "pm-studio-plus",
    "backend",
    "grading",
    "staff-test-results",
    "local-secrets",
}
FORBIDDEN_SUFFIXES = {".docx", ".xlsx", ".pptx", ".pem", ".key"}
SECRET_VALUE_PATTERNS = (
    re.compile(r"v550_ct_[A-Za-z0-9_-]{32,}"),
    re.compile(r"V550_[A-Za-z0-9_-]{24,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def main() -> int:
    errors: list[str] = []
    for required in REQUIRED:
        if not required.is_file():
            errors.append(f"missing required file: {required.relative_to(ROOT)}")

    files = [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]
    for path in files:
        relative = path.relative_to(ROOT)
        if FORBIDDEN_PARTS.intersection(relative.parts):
            errors.append(f"forbidden instructor-only path: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden file type: {relative}")
        if path.name.startswith(".env") or "student-key" in path.name.lower():
            errors.append(f"forbidden local credential file: {relative}")
        if path.suffix.lower() in {".md", ".py", ".sh", ".yaml", ".json", ".txt"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"non-UTF-8 text file: {relative}")
                continue
            for pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(text):
                    errors.append(f"possible credential value in: {relative}")

    for script in ROOT.rglob("*.py"):
        if ".git" not in script.parts:
            try:
                ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
            except (SyntaxError, UnicodeDecodeError) as error:
                errors.append(f"Python syntax failed for {script.relative_to(ROOT)}: {error}")

    skill = ROOT / "skills" / "v550-scope-advisor" / "SKILL.md"
    if skill.is_file() and "name: v550-scope-advisor" not in skill.read_text(encoding="utf-8"):
        errors.append("skill frontmatter name is invalid")

    if errors:
        print("STUDENT PACKAGE CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"STUDENT PACKAGE CHECK PASSED: {len(files)} files scanned")
    print("No instructor-only paths, credential files, or high-signal secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

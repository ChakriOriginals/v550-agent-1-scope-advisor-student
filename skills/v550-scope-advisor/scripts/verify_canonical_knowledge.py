#!/usr/bin/env python3
"""Verify canonical V550 course references in the standalone student skill."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = SKILL_ROOT / "references" / "canonical-source-manifest.json"


def safe_reference(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("canonical source path must be non-empty text")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"canonical source path is unsafe: {value!r}")
    resolved = (SKILL_ROOT / relative).resolve()
    resolved.relative_to((SKILL_ROOT / "references").resolve())
    return resolved


def verify() -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"valid": False, "errorCount": 1, "errors": [{"path": str(MANIFEST), "message": str(exc)}]}
    if manifest.get("schema_version") != "2.0.0":
        errors.append({"path": "$", "message": "manifest schema_version must be 2.0.0"})
    sources = manifest.get("canonical_sources")
    if not isinstance(sources, list) or len(sources) != 4:
        errors.append({"path": "$.canonical_sources", "message": "exactly four canonical sources are required"})
        sources = []
    observed: list[dict[str, Any]] = []
    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            errors.append({"path": f"$.canonical_sources[{index}]", "message": "entry must be an object"})
            continue
        try:
            path = safe_reference(item.get("source"))
        except (ValueError, OSError) as exc:
            errors.append({"path": f"$.canonical_sources[{index}].source", "message": str(exc)})
            continue
        if not path.is_file():
            errors.append({"path": item.get("source", ""), "message": "canonical source is missing"})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        equal = digest == item.get("sha256")
        observed.append({"source": item.get("source"), "sha256": digest, "matches": equal})
        if not equal:
            errors.append({"path": item.get("source", ""), "message": "canonical source digest mismatch"})
    return {"valid": not errors, "sourceCount": len(observed), "sources": observed, "errorCount": len(errors), "errors": errors}


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

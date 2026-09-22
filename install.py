#!/usr/bin/env python3
"""Install the bundled V550 Scope Advisor without handling credentials."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "skills" / "v550-scope-advisor"


def target_root() -> Path:
    """Return the documented per-user skill directory for ChatGPT and Codex."""

    configured = os.environ.get("V550_SKILLS_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".agents" / "skills"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    if not (SOURCE / "SKILL.md").is_file():
        print("Install failed: bundled skill is incomplete.", file=sys.stderr)
        return 2
    destination = target_root() / "v550-scope-advisor"
    if destination.exists():
        print(
            f"Install stopped: {destination} already exists. Move the old folder "
            "aside, verify this package, and rerun the installer.",
            file=sys.stderr,
        )
        return 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, destination)
    print(f"Installed v550-scope-advisor at {destination}")
    print("This local-only skill requires no course credential or external service.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

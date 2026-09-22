"""Regression tests for the student skill installer."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.py"


class InstallerTests(unittest.TestCase):
    def test_installs_into_documented_user_skill_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary) / ".agents" / "skills"
            environment = os.environ.copy()
            environment["V550_SKILLS_HOME"] = str(skill_root)
            completed = subprocess.run(
                ["python3", str(INSTALLER)],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            installed_skill = skill_root / "v550-scope-advisor" / "SKILL.md"
            installed_generator = (
                skill_root
                / "v550-scope-advisor"
                / "scripts"
                / "generate_review_bundle.py"
            )
            installed_verifier = (
                skill_root
                / "v550-scope-advisor"
                / "scripts"
                / "verify_review_bundle.py"
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(installed_skill.is_file())
            self.assertTrue(installed_generator.is_file())
            self.assertTrue(installed_verifier.is_file())
            self.assertIn(str(skill_root / "v550-scope-advisor"), completed.stdout)


if __name__ == "__main__":
    unittest.main()

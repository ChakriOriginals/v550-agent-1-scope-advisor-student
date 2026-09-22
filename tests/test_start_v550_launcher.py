"""Regression tests for the local V550 launchers."""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI_LAUNCHER = ROOT / "start-v550.sh"
DESKTOP_LAUNCHER = ROOT / "start-v550-desktop.sh"


class LauncherTests(unittest.TestCase):
    def test_shell_syntax(self) -> None:
        for launcher in (CLI_LAUNCHER, DESKTOP_LAUNCHER):
            with self.subTest(launcher=launcher.name):
                completed = subprocess.run(
                    ["sh", "-n", str(launcher)], capture_output=True, text=True, check=False
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_cli_diagnostic_requires_no_course_credential(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_cli = Path(temporary) / "codex"
            fake_cli.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_cli.chmod(fake_cli.stat().st_mode | stat.S_IXUSR)
            environment = os.environ.copy()
            environment["V550_CODEX_CLI"] = str(fake_cli)
            completed = subprocess.run(
                [str(CLI_LAUNCHER), "--check-cli"],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Codex CLI detected.", completed.stdout)

    def test_cli_launcher_starts_in_repository_without_remote_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_cli = Path(temporary) / "codex"
            fake_cli.write_text(
                "#!/bin/sh\n"
                f"[ \"$PWD\" = \"{ROOT}\" ] || exit 41\n"
                "printf 'LOCAL_CODEX_STARTED\\n'\n",
                encoding="utf-8",
            )
            fake_cli.chmod(fake_cli.stat().st_mode | stat.S_IXUSR)
            environment = os.environ.copy()
            environment["V550_CODEX_CLI"] = str(fake_cli)
            completed = subprocess.run(
                [str(CLI_LAUNCHER)],
                cwd=ROOT.parent,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("LOCAL_CODEX_STARTED", completed.stdout)

    def test_desktop_launcher_starts_without_course_credential(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_app = Path(temporary) / "ChatGPT"
            fake_app.write_text(
                "#!/bin/sh\n"
                f"[ \"$PWD\" = \"{ROOT}\" ] || exit 51\n"
                "printf 'LOCAL_DESKTOP_STARTED\\n'\n",
                encoding="utf-8",
            )
            fake_app.chmod(fake_app.stat().st_mode | stat.S_IXUSR)
            environment = os.environ.copy()
            environment["V550_CHATGPT_EXECUTABLE"] = str(fake_app)
            completed = subprocess.run(
                [str(DESKTOP_LAUNCHER)],
                cwd=ROOT.parent,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("LOCAL_DESKTOP_STARTED", completed.stdout)


if __name__ == "__main__":
    unittest.main()

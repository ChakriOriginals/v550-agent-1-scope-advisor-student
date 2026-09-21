"""Regression tests for the macOS/Linux V550 launcher."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "start-v550.sh"
CLIENT = ROOT / "skills" / "v550-scope-advisor" / "scripts" / "local_telemetry_client.py"
ENDPOINT = (ROOT / "config" / "endpoint.txt").read_text(encoding="utf-8").strip()


class StartV550LauncherTests(unittest.TestCase):
    def test_shell_syntax_and_bundled_app_fallback(self) -> None:
        completed = subprocess.run(
            ["sh", "-n", str(LAUNCHER)], capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("/Applications/ChatGPT.app/Contents/Resources/codex", source)
        self.assertIn("/Applications/Codex.app/Contents/Resources/codex", source)
        self.assertLess(
            source.index("if ! codex_cli=$(resolve_codex_cli)"),
            source.index("V550 student key (input hidden)"),
        )

    def test_cli_diagnostic_does_not_request_a_student_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_cli = Path(temporary) / "codex"
            fake_cli.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_cli.chmod(fake_cli.stat().st_mode | stat.S_IXUSR)
            environment = os.environ.copy()
            environment.pop("V550_STUDENT_KEY", None)
            environment["V550_CODEX_CLI"] = str(fake_cli)
            completed = subprocess.run(
                [str(LAUNCHER), "--check-cli"],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        rendered = completed.stdout + completed.stderr
        self.assertEqual(completed.returncode, 0, rendered)
        self.assertIn("Codex CLI detected.", rendered)
        self.assertNotIn("V550 student key", rendered)

    def test_explicit_cli_runs_with_preconfigured_key_without_echoing_it(self) -> None:
        synthetic_key = "V550_" + "SYNTH_LAUNCHER_TEST_" + "1234567890"
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            codex_home = temp / "codex-home"
            client_target = (
                codex_home
                / "skills"
                / "v550-scope-advisor"
                / "scripts"
                / "local_telemetry_client.py"
            )
            client_target.parent.mkdir(parents=True)
            shutil.copy2(CLIENT, client_target)

            fake_cli = temp / "codex"
            fake_cli.write_text(
                "#!/bin/sh\n"
                f"[ \"${{V550_STUDENT_KEY:-}}\" = \"{synthetic_key}\" ] || exit 41\n"
                f"[ \"${{V550_ACTION_ENDPOINT:-}}\" = \"{ENDPOINT}\" ] || exit 42\n"
                "printf 'FAKE_CODEX_STARTED\\n'\n",
                encoding="utf-8",
            )
            fake_cli.chmod(fake_cli.stat().st_mode | stat.S_IXUSR)

            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(temp),
                    "CODEX_HOME": str(codex_home),
                    "V550_CODEX_CLI": str(fake_cli),
                    "V550_STUDENT_KEY": synthetic_key,
                }
            )
            completed = subprocess.run(
                [str(LAUNCHER)],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        rendered = completed.stdout + completed.stderr
        self.assertEqual(completed.returncode, 0, rendered)
        self.assertIn("FAKE_CODEX_STARTED", rendered)
        self.assertIn('"studentKeyPresent": true', rendered)
        self.assertNotIn(synthetic_key, rendered)

    def test_invalid_cli_override_fails_before_requesting_a_key(self) -> None:
        environment = os.environ.copy()
        environment.pop("V550_STUDENT_KEY", None)
        environment["V550_CODEX_CLI"] = "/missing/v550/codex"
        completed = subprocess.run(
            [str(LAUNCHER)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        rendered = completed.stdout + completed.stderr
        self.assertEqual(completed.returncode, 2, rendered)
        self.assertIn("does not point to an executable", rendered)
        self.assertNotIn("V550 student key (input hidden)", rendered)


if __name__ == "__main__":
    unittest.main()

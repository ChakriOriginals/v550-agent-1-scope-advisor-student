"""Offline tests for standardized V550 review bundles."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "v550-scope-advisor" / "scripts"
GENERATOR = SCRIPTS / "generate_review_bundle.py"
VERIFIER = SCRIPTS / "verify_review_bundle.py"


def record(kind: str, payload: dict[str, object], ordinal: int) -> dict[str, object]:
    return {
        "timestamp": f"2026-09-21T12:{ordinal:02d}:00Z",
        "type": kind,
        "payload": payload,
        "ordinal": ordinal,
    }


def write_session(path: Path, workspace: Path, *, include_review: bool = True) -> None:
    rows = [
        record(
            "session_meta",
            {
                "id": "session-test-001",
                "timestamp": "2026-09-21T12:00:00Z",
                "cwd": str(workspace),
                "originator": "Codex Desktop",
            },
            1,
        ),
        record(
            "response_item",
            {
                "type": "message",
                "role": "developer",
                "content": [{"type": "input_text", "text": "HIDDEN TEST INSTRUCTION"}],
            },
            2,
        ),
        record(
            "response_item",
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Evaluate Gate 1 using my work."}],
            },
            3,
        ),
        record(
            "response_item",
            {
                "type": "message",
                "role": "assistant",
                "phase": "final",
                "content": [
                    {
                        "type": "output_text",
                        "text": (
                            "Gate: 1 - Big 5 Pre-Planning\n"
                            "Progress: All required items are present.\n"
                            "What still needs attention: Nothing blocking.\n"
                            "Ready to move on: YES — Gate OPEN\n"
                            "Optional advice: This advice does not block you.\n"
                            "Your next move: Begin Gate 2."
                        ),
                    }
                ],
            },
            4,
        ),
    ]
    if include_review:
        rows.extend(
            [
                record(
                    "response_item",
                    {
                        "type": "message",
                        "role": "assistant",
                        "phase": "final",
                        "content": [
                            {
                                "type": "output_text",
                                "text": (
                                    "## V550 Final Learning Review\n\n"
                                    "Completion state: Session ended after Gate 1.\n"
                                    "Demonstrated learning: The student distinguished authority from influence.\n"
                                    "Next behavior: Carry source and verification evidence into Gate 2."
                                ),
                            }
                        ],
                    },
                    5,
                ),
                record(
                    "response_item",
                    {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "Generate my review bundle"}],
                    },
                    6,
                ),
            ]
        )
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class ReviewBundleTests(unittest.TestCase):
    def generate(self, temporary: str, *, include_review: bool = True) -> tuple[subprocess.CompletedProcess[str], Path]:
        base = Path(temporary)
        workspace = base / "workspace"
        workspace.mkdir()
        session = base / "rollout-test.jsonl"
        output = base / "output"
        write_session(session, workspace, include_review=include_review)
        completed = subprocess.run(
            [
                "python3",
                str(GENERATOR),
                "--workspace",
                str(workspace),
                "--session-file",
                str(session),
                "--output-root",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return completed, output

    def test_generates_complete_visible_transcript_and_valid_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, _ = self.generate(temporary)
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            result = json.loads(completed.stdout)
            bundle = Path(result["bundleDirectory"])
            archive = Path(result["archive"])
            record_data = json.loads((bundle / "V550_REVIEW_RECORD.json").read_text(encoding="utf-8"))
            rendered = "\n".join(item["text"] for item in record_data["transcript"])
            self.assertIn("Evaluate Gate 1", rendered)
            self.assertIn("YES — Gate OPEN", rendered)
            self.assertIn("Generate my review bundle", rendered)
            self.assertNotIn("HIDDEN TEST INSTRUCTION", rendered)
            self.assertEqual(record_data["gate_outcomes"][0]["latest_status"], "OPEN")
            self.assertEqual(record_data["gate_outcomes"][1]["latest_status"], "NOT REVIEWED")
            self.assertFalse(os.stat(bundle / "V550_REVIEW_SHEET.html").st_mode & stat.S_IWUSR)

            verified = subprocess.run(
                ["python3", str(VERIFIER), str(archive)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verified.returncode, 0, verified.stderr + verified.stdout)
            self.assertTrue(json.loads(verified.stdout)["valid"])

    def test_tampered_review_sheet_fails_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, _ = self.generate(temporary)
            self.assertEqual(completed.returncode, 0, completed.stdout)
            bundle = Path(json.loads(completed.stdout)["bundleDirectory"])
            sheet = bundle / "V550_REVIEW_SHEET.html"
            sheet.chmod(stat.S_IRUSR | stat.S_IWUSR)
            sheet.write_text(sheet.read_text(encoding="utf-8") + "\nmodified", encoding="utf-8")
            verified = subprocess.run(
                ["python3", str(VERIFIER), str(bundle)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verified.returncode, 1, verified.stdout)
            self.assertIn("Hash mismatch", verified.stdout)

    def test_unexpected_file_fails_standardized_bundle_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, _ = self.generate(temporary)
            self.assertEqual(completed.returncode, 0, completed.stdout)
            bundle = Path(json.loads(completed.stdout)["bundleDirectory"])
            bundle.chmod(stat.S_IRWXU)
            (bundle / "extra.txt").write_text("not part of the standard", encoding="utf-8")
            verified = subprocess.run(
                ["python3", str(VERIFIER), str(bundle)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verified.returncode, 1, verified.stdout)
            self.assertIn("Unexpected files", verified.stdout)

    def test_noncanonical_generator_hash_fails_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, _ = self.generate(temporary)
            self.assertEqual(completed.returncode, 0, completed.stdout)
            bundle = Path(json.loads(completed.stdout)["bundleDirectory"])
            manifest_path = bundle / "V550_REVIEW_MANIFEST.json"
            manifest_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["generator_sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            verified = subprocess.run(
                ["python3", str(VERIFIER), str(bundle)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verified.returncode, 1, verified.stdout)
            self.assertIn("Generator hash", verified.stdout)

    def test_refuses_export_without_final_learning_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, _ = self.generate(temporary, include_review=False)
            self.assertEqual(completed.returncode, 1, completed.stdout)
            self.assertIn("standardized final learning review", completed.stdout)


if __name__ == "__main__":
    unittest.main()

# V550 Scope Advisor — local student practice

This repository installs the Stage 1 Scope Advisor as a fully local Codex skill.
Students work through the frozen **Allocating the Waldron** scenario using six
ordered Scope of Work gates. The advisor teaches, preserves student-authored work,
evaluates only after a ready signal, and never writes the assignment for the
student.

There is no remote faculty service, roster lookup, course credential, or
automatic grade connection.

## Install

You need Git, Python 3.11 or newer, and either ChatGPT Desktop with Codex or the
Codex CLI.

```bash
git clone https://github.com/ChakriOriginals/v550-agent-1-scope-advisor-student.git
cd v550-agent-1-scope-advisor-student
python3 tools/verify_package.py
python3 install.py
```

The installer copies the skill to:

```text
~/.agents/skills/v550-scope-advisor
```

## Start in ChatGPT Desktop on macOS

```bash
./start-v550-desktop.sh
```

In ChatGPT Desktop:

1. Select **Codex**.
2. Open this repository as a local folder.
3. Confirm **v550 Scope Advisor** appears under **Skills**.
4. Start a new local chat and send:

```text
Use $v550-scope-advisor to help me practice Stage 1 Scope of Work in Guided mode.
```

For the terminal interface, run `./start-v550.sh` and use the same prompt.

## Learning flow

The advisor runs these gates in order:

1. Big 5 Pre-Planning
2. Requirements
3. Expectations
4. Goals & Objectives
5. Scope of Work
6. Work Breakdown Structure, including internal Gate 6B

The student drafts first. A gate is evaluated only after the student explicitly
asks for review. All frozen required items must pass before the gate opens.

## Final review bundle

At completion—or when ending an incomplete session—the advisor produces a
standardized `V550 Final Learning Review`. The student then sends:

```text
Generate my review bundle
```

The local exporter creates a read-only folder and ZIP under
`V550 Review Bundles/`. The bundle contains:

- a human-readable HTML review sheet;
- the complete visible student/advisor transcript;
- latest formal status for all six gates;
- the advisor's final qualitative feedback;
- a canonical JSON record and SHA-256 manifest.

System/developer instructions, hidden reasoning, tool calls, and tool output are
excluded.

Local permissions and hashes discourage edits and detect mismatches, but no file
on a student-owned computer can be made truly uneditable without an
instructor-controlled signing or submission service. The bundle states this
limitation explicitly.

See [STUDENT_SETUP_GUIDE.md](STUDENT_SETUP_GUIDE.md) for full setup,
troubleshooting, updating, and submission instructions.

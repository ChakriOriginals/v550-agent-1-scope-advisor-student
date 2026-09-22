# V550 Scope Advisor: Student Setup Guide

The V550 Stage 1 Scope Advisor is a local learning partner for the six Scope of
Work gates in the frozen Allocating the Waldron scenario. It does not complete
the assignment, assign a grade, or send course activity to a remote course service.

## Requirements

- access to the private course GitHub repository;
- Git;
- Python 3.11 or newer;
- ChatGPT Desktop with Codex, or the Codex CLI.

Check Git and Python:

```bash
git --version
python3 --version
```

## Install on macOS or Linux

```bash
git clone https://github.com/ChakriOriginals/v550-agent-1-scope-advisor-student.git
cd v550-agent-1-scope-advisor-student
python3 tools/verify_package.py
python3 install.py
```

Continue only when verification reports `STUDENT PACKAGE CHECK PASSED`. The
skill is installed at `~/.agents/skills/v550-scope-advisor`.

If an older copy exists, preserve it as a backup before reinstalling:

```bash
mv "$HOME/.agents/skills/v550-scope-advisor" \
  "$HOME/.agents/skills/v550-scope-advisor.backup"
python3 install.py
```

Do not delete an existing backup. Ask the instructor or TA for help if the backup
name already exists.

## Start with ChatGPT Desktop on macOS

Check the app installation:

```bash
./start-v550-desktop.sh --check-desktop
```

Then launch:

```bash
./start-v550-desktop.sh
```

In ChatGPT Desktop:

1. Select **Codex**.
2. Choose **Open folder** and select the cloned repository.
3. Open **Skills** and confirm **v550 Scope Advisor** is listed.
4. Start a new local chat.
5. Send:

```text
Use $v550-scope-advisor to help me practice Stage 1 Scope of Work in Guided mode.
```

## Start with Codex CLI

```bash
./start-v550.sh --check-cli
./start-v550.sh
```

Then use the same advisor prompt.

## Windows PowerShell

```powershell
git clone https://github.com/ChakriOriginals/v550-agent-1-scope-advisor-student.git
Set-Location v550-agent-1-scope-advisor-student
python tools/verify_package.py
python install.py
codex
```

Open the cloned repository in Codex and use the advisor prompt above.

## During the learning session

The advisor first explains the local transcript boundary. The final submitted
review contains the complete visible conversation, so do not enter passwords,
credentials, or sensitive personal, medical, financial, disciplinary,
immigration, disability, employment, or security information.

The advisor then runs exactly six gates in order. Guided mode asks one focused
question at a time. Independent mode provides the complete blank structure. The
student authors every assessed decision.

To request a formal gate evaluation, use a clear signal such as:

```text
Evaluate Gate 1
```

## Generate the final review sheet

After Gate 6 opens—or when the student asks to end an incomplete session—the
advisor produces `## V550 Final Learning Review` and asks for a new message.
Send exactly:

```text
Generate my review bundle
```

The generated files appear under:

```text
V550 Review Bundles/
```

Submit the generated ZIP unless the instructor requests the complete folder.
The ZIP contains the review sheet, canonical transcript/evaluation record,
integrity manifest, and submission notes.

Verify a bundle locally with:

```bash
python "$HOME/.agents/skills/v550-scope-advisor/scripts/verify_review_bundle.py" \
  "V550 Review Bundles/v550-review-....zip"
```

A valid result confirms internal file consistency. It does not cryptographically
prove authorship because the bundle is generated on the student's computer.

## Troubleshooting

### The skill is not visible

```bash
test -f "$HOME/.agents/skills/v550-scope-advisor/SKILL.md" && echo "Skill installed"
```

Quit and reopen ChatGPT Desktop after installing or updating the skill.

### The review generator cannot find the session

Confirm the repository was opened as the current **local Codex folder** and run
the generation request from that same chat. A remote/cloud chat does not use the
local session location required by the exporter.

### The final learning review is missing

Ask the advisor to end the learning session. Wait until it produces the exact
`V550 Final Learning Review` heading, then send `Generate my review bundle` in a
new message.

### A bundle already exists

The exporter never overwrites a prior bundle. Keep the existing submission
snapshot and generate from a new Codex session if another attempt is required.

## Update later

```bash
git pull --ff-only
python3 tools/verify_package.py
```

Move the installed skill to a new backup name, rerun `python3 install.py`, then
restart ChatGPT Desktop or Codex.

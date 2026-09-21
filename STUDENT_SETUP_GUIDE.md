# V550 Scope Advisor: Student Setup Guide

This guide installs the V550 Stage 1 Scope Advisor as a local Codex skill. The
advisor helps you practice the six Scope of Work gates. It does not complete the
assignment for you, submit to Canvas, or assign a grade.

## Before you begin

You need:

- access to the private course GitHub repository;
- your individual V550 student key from the instructor or TA;
- Git;
- Python 3.11 or newer;
- `curl`;
- the ChatGPT desktop app or Codex CLI.

Check the required programs:

```bash
git --version
python3 --version
curl --version
```

If one of these commands is unavailable, contact the instructor or TA before
continuing.

## macOS or Linux

### 1. Download the course repository

```bash
git clone https://github.com/ChakriOriginals/v550-agent-1-scope-advisor-student.git
cd v550-agent-1-scope-advisor-student
```

GitHub may ask you to sign in because this is a private course repository.

On macOS, confirm at least one launch surface is available:

```bash
./start-v550-desktop.sh --check-desktop
./start-v550.sh --check-cli
```

You only need one of these checks to pass.

### 2. Verify the package

```bash
python3 tools/verify_package.py
```

Continue only when the command reports `STUDENT PACKAGE CHECK PASSED`.

### 3. Install the skill

```bash
python3 install.py
```

The installer copies the skill into the documented user skill folder:

```text
~/.agents/skills/v550-scope-advisor
```

It does not ask for or save your student key.

### 4A. Start ChatGPT Desktop for V550 practice on macOS

First choose **ChatGPT > Quit ChatGPT** so no existing app process remains. Then
run:

```bash
./start-v550-desktop.sh
```

Enter your individual student key at the hidden prompt. Nothing will appear while
you type. Press Enter when finished. The launcher starts a new ChatGPT Desktop
process with the key and endpoint in that process environment only. It does not
write the key to disk.

In ChatGPT Desktop:

1. Select **Codex**, choose **Open folder**, and select this cloned repository.
2. Open **Skills** in the sidebar and confirm **v550 Scope Advisor** is listed.
3. Start a local Codex chat and type `$` to select `v550-scope-advisor`.
4. Send:

```text
Use $v550-scope-advisor to help me practice Stage 1 Scope of Work in Guided mode.
```

The advisor will explain the limited telemetry and ask for consent before its
first write. You may decline telemetry and continue practicing locally. Keep the
Terminal window open while using this specially launched app, and quit ChatGPT
when the V550 practice session is finished.

### 4B. Start Codex CLI for V550 practice

```bash
./start-v550.sh
```

Enter your individual student key at the hidden prompt. Nothing will appear while
you type. Press Enter when finished. The key exists only in the launched process
and is not written to the repository. On macOS, the launcher also detects the
Codex CLI bundled inside the standard ChatGPT or Codex application even when it is
missing from Terminal's `PATH`.

### 5. Start the advisor

At the Codex prompt, enter:

```text
Use $v550-scope-advisor to help me practice Stage 1 Scope of Work in Guided mode.
```

The advisor will explain the limited telemetry and ask for consent before its first
write. You may decline telemetry and continue practicing locally.

## Windows PowerShell

### 1. Download, verify, and install

```powershell
git clone https://github.com/ChakriOriginals/v550-agent-1-scope-advisor-student.git
Set-Location v550-agent-1-scope-advisor-student
python tools/verify_package.py
python install.py
```

Continue only when verification reports `STUDENT PACKAGE CHECK PASSED`.

### 2. Start a credential-safe session

Run the following from the repository folder. The student-key prompt is hidden.

```powershell
$env:V550_ACTION_ENDPOINT = Get-Content .\config\endpoint.txt -First 1
$secureKey = Read-Host "V550 student key" -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
    $env:V550_STUDENT_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
}
python "$env:USERPROFILE\.agents\skills\v550-scope-advisor\scripts\local_telemetry_client.py" --check-config
codex
Remove-Item Env:V550_STUDENT_KEY, Env:V550_ACTION_ENDPOINT -ErrorAction SilentlyContinue
```

Then use the CLI advisor prompt shown above. Run Codex from this PowerShell
window; an already-running ChatGPT Desktop session will not inherit these temporary
environment variables.

## What telemetry contains

After consent, the advisor may send minimized, pseudonymous events such as session
start, gate lifecycle, and report issuance. It must not send transcripts, full
drafts, personal information, sensitive details, secrets, or grades.

Students cannot access the faculty workbook or dashboard. The endpoint accepts
writes only after validating an active, revocable student key.

## Protect your student key

- Do not paste it into a Codex or ChatGPT conversation.
- Do not put it in a file, screenshot, Git commit, issue, email thread, or Living
  Project File.
- Do not share it with another student.
- If it is lost or exposed, contact the instructor or TA for revocation and
  replacement.
- There is no PIN and no `classToken`; your individual student key is the only
  client credential.

## Common problems

### `STUDENT_KEY_NOT_ALLOWED`

Re-enter the key carefully. If the error continues, ask the instructor or TA to
confirm that your key is active.

### `The V550 skill is not installed`

Return to the repository folder and run:

```bash
python3 install.py
```

On Windows, use `python install.py`.

### The installer says the skill already exists

The installer never overwrites an existing copy. Move the existing folder aside,
then rerun the installer.

macOS or Linux:

```bash
mv "$HOME/.agents/skills/v550-scope-advisor" "$HOME/.agents/skills/v550-scope-advisor.backup"
python3 install.py
```

Windows PowerShell:

```powershell
Rename-Item "$env:USERPROFILE\.agents\skills\v550-scope-advisor" "v550-scope-advisor.backup"
python install.py
```

If a backup with that name already exists, ask the instructor or TA for help rather
than deleting folders.

### Telemetry is temporarily unavailable

Continue practicing locally. The advisor must not claim that the faculty dashboard
was updated unless the server returned a successful acknowledgement.

### You see an IU login page or HTML instead of JSON

Stop the telemetry attempt and notify the instructor or TA. Your local practice and
Markdown checkpoint can continue.

### `Codex CLI was not found`

Update to the latest ChatGPT/Codex app or install the Codex CLI, then rerun
`./start-v550.sh`. The launcher checks both Terminal's `PATH` and the standard
macOS application locations. If the message continues, send the error text to the
instructor or TA; do not send your student key.

You can check CLI discovery without entering a student key:

```bash
./start-v550.sh --check-cli
```

### ChatGPT Desktop says it is already running

Choose **ChatGPT > Quit ChatGPT**, wait for the app to close, and rerun:

```bash
./start-v550-desktop.sh
```

The launcher deliberately refuses to reuse an already-running app because that
process would not inherit the temporary student key.

### The skill is not visible in ChatGPT Desktop

Confirm the install exists, then quit and relaunch the app:

```bash
test -f "$HOME/.agents/skills/v550-scope-advisor/SKILL.md" && echo "Skill installed"
./start-v550-desktop.sh
```

Open **Skills** in the sidebar after the repository folder is open. In a local
Codex chat or Codex CLI, type `$` to select the skill; in the CLI you can also
run `/skills`.

## Updating later

From the repository folder:

```bash
git pull --ff-only
python3 tools/verify_package.py
```

Move the installed skill aside as described above, then run the installer again.
Never overwrite or delete an existing skill folder unless the instructor or TA has
confirmed the update procedure.

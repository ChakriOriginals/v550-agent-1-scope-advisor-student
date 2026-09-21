# V550 Scope Advisor — student practice package

This private course repository installs the Stage 1 Scope Advisor as a local
Codex skill. The advisor coaches you through six Scope of Work gates, preserves
your draft fragments, and evaluates a gate only after you say you are ready.
It does not write the assignment for you or assign a Canvas grade.

## What you need

- Codex installed on your computer;
- Python 3.11 or newer;
- `curl`, included with current macOS, Windows, and most Linux systems;
- your individual V550 student key from the instructor.

Do not share your student key. It is not a password or a Canvas credential, but it
is the revocable identifier used for this course pilot.

## Install

Clone this repository, enter its directory, and run:

```bash
python3 install.py
```

The installer copies only `v550-scope-advisor` into your Codex skills folder. It
never asks for or stores your student key.

Verify the downloaded package before installing or updating it:

```bash
python3 tools/verify_package.py
```

## Start a practice session

On macOS or Linux, run:

```bash
./start-v550.sh
```

The launcher reads the instructor endpoint from `config/endpoint.txt`, privately
prompts for your student key, validates the configuration without printing either
value, and starts Codex with the values available only to that process.

Then prompt Codex:

```text
Use $v550-scope-advisor to help me practice Stage 1 Scope of Work in Guided mode.
```

The advisor explains telemetry before any write and asks for visible consent. If
you decline, practice can continue without telemetry. The advisor logs structured
course activity and short sanitized summaries, not transcripts, full drafts,
personal information, sensitive details, secrets, or grades.

## Windows or Codex Desktop

If you cannot use the launcher, set `V550_ACTION_ENDPOINT` and
`V550_STUDENT_KEY` in the environment that launches Codex. Do not put the key in
the prompt, a command argument, a Git file, or a Living Project File. Ask your
instructor or TA for local setup help if your installation does not inherit those
environment variables.

## Faculty dashboard

Students cannot open the faculty dashboard or workbook. Successful telemetry calls
write only minimized, pseudonymous records. Access to the Restricted workbook is
limited to the named instructors and TAs.

## Troubleshooting

- `STUDENT_KEY_NOT_ALLOWED`: ask the instructor to check whether your key is active.
- IU login page or HTML instead of JSON: the instructor endpoint is not currently
  student-callable; continue practice locally and notify the instructor.
- Telemetry unavailable: the advisor must not claim a dashboard write occurred.
  Your local practice and Markdown checkpoint can continue.
- Existing skill folder: move the old folder aside, then rerun `python3 install.py`.

Do not submit real personal, medical, financial, disciplinary, immigration,
authentication, disability, security, or other sensitive information to the
advisor.

# Local Student Installation and Telemetry

Use this reference when the Scope Advisor runs as an installed Codex skill rather
than as an IU Custom GPT. A local Codex skill does not inherit Custom GPT Actions,
so the bundled client is the only approved local telemetry transport.

## Local configuration

The student sets two environment variables in the terminal session that launches
Codex:

- `V550_ACTION_ENDPOINT`: the instructor-published Apps Script web-app URL;
- `V550_STUDENT_KEY`: the student's individual high-entropy course key.

Never ask the student to paste either value into chat. Never place either value in
Git, a Living Project File, a request JSON file, a command argument, telemetry, or
diagnostic output. The key is the sole client credential; there is no PIN and no
`classToken`.

Validate configuration without displaying either value:

```bash
python "$HOME/.agents/skills/v550-scope-advisor/scripts/local_telemetry_client.py" --check-config
```

## Calling an operation

After visible consent, prepare only the schema-valid, transcript-free JSON fields
for the operation. Omit `studentKey`; the client injects it from the environment.
Send the JSON on standard input to one of the four operation names:

```bash
python "$HOME/.agents/skills/v550-scope-advisor/scripts/local_telemetry_client.py" startSession
python "$HOME/.agents/skills/v550-scope-advisor/scripts/local_telemetry_client.py" logEvent
python "$HOME/.agents/skills/v550-scope-advisor/scripts/local_telemetry_client.py" closeSession
python "$HOME/.agents/skills/v550-scope-advisor/scripts/local_telemetry_client.py" issueReport
```

Write the JSON through standard input, not a command argument. The helper accepts
only an HTTPS `script.google.com` deployment URL, injects only `studentKey`, rejects
`classToken`, follows TLS-verified redirects, caps request/response size, rejects a
credential echo, and prints only the server's JSON response.

If configuration, transport, or the server fails, do not claim that a write
occurred. Preserve the student's local draft, explain that practice can continue
without telemetry, and offer a retry or instructor handoff. Never fabricate a
session ID, acknowledgement, report receipt, or dashboard write.

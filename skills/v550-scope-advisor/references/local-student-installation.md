# Local Student Installation

The V550 Scope Advisor runs entirely inside the student's local Codex workspace.
It requires no remote course service, credential, roster lookup, or faculty data
store.

## Install and launch

From the cloned course repository:

```bash
python3 tools/verify_package.py
python3 install.py
./start-v550-desktop.sh
```

In ChatGPT Desktop, select Codex, open the cloned repository as a local folder,
start a new chat, and invoke:

```text
Use $v550-scope-advisor to help me practice Stage 1 Scope of Work in Guided mode.
```

For the terminal interface, use `./start-v550.sh` and the same prompt.

## Local files

- The installed skill lives at `~/.agents/skills/v550-scope-advisor`.
- The Living Project File stays in the current student's local workspace.
- Review bundles are written under `V550 Review Bundles/` in that workspace and
  are ignored by Git.
- Codex maintains its ordinary local session history under the user's Codex data
  directory. The review exporter reads only the current workspace's visible
  student/advisor messages.

No course conversation or review bundle is automatically sent to an instructor.
The student submits the generated ZIP using the instructor's chosen course
submission method.

## Session closeout

After the advisor displays `## V550 Final Learning Review`, the student sends:

```text
Generate my review bundle
```

The advisor runs the bundled local exporter and returns the ZIP path. Read
`local-review-bundles.md` for the exact contents and integrity boundary.

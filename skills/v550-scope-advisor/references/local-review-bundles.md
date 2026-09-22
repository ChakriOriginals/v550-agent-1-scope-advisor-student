# Local Review Bundles

Use this reference when ending a V550 learning session or verifying a submitted
review bundle. The workflow is fully local and sends no course data to a remote
service.

## Required two-turn closeout

The exporter reads the actual Codex session record, so the final evaluation must
exist before export:

1. The advisor produces a visible message headed exactly
   `## V550 Final Learning Review`.
2. That review states the completion condition, latest status of Gates 1–6,
   demonstrated learning, important revisions, unresolved required items, and one
   concrete next behavior. It contains no grade or hidden reasoning.
3. The advisor asks the student to send `Generate my review bundle` as a new
   message.
4. On that next turn, run the bundled generator from the current local project:

```bash
python "$HOME/.agents/skills/v550-scope-advisor/scripts/generate_review_bundle.py" --workspace "$PWD"
```

The final administrative response that returns the file path is outside the
evaluated snapshot. All earlier visible student and advisor messages are included.

## Standardized contents

Each new `V550 Review Bundles/v550-review-*` directory and ZIP contains exactly:

- `V550_REVIEW_SHEET.html`: human-readable review, gate table, final feedback,
  and complete visible transcript;
- `V550_REVIEW_RECORD.json`: canonical structured record;
- `V550_REVIEW_MANIFEST.json`: file sizes and SHA-256 integrity values;
- `README.txt`: submission and integrity explanation.

The exporter includes visible `user` and `assistant` messages only. It excludes
system/developer instructions, hidden reasoning, tool calls, and tool output.
Non-text chat items receive a visible placeholder rather than being silently
represented as text.

The generator never overwrites an existing bundle. It marks the output files
read-only and creates a ZIP for submission.

## Verification

Faculty or students can verify either the folder or ZIP:

```bash
python "$HOME/.agents/skills/v550-scope-advisor/scripts/verify_review_bundle.py" \
  "V550 Review Bundles/v550-review-....zip"
```

A valid result proves that the submitted files are internally consistent with
their included hashes. It does not prove identity or authorship. A student owns
their computer and can change permissions, local session files, code, and hashes.
True non-editability or authenticated authorship requires a separate
instructor-controlled submission/signing service, which this local-only package
does not use.

## Privacy boundary

The bundle intentionally contains the complete visible conversation. Before Gate
1, warn the student not to enter passwords, credentials, personal identifiers not
needed for submission, or sensitive personal, medical, financial, disciplinary,
immigration, disability, employment, or security details.

Do not include hidden reasoning, unrelated chat history, another student's data,
or content from any session other than the current local workspace session.

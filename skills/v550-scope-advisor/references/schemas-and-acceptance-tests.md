# Local Schemas and Acceptance Tests

## Frozen gate boundary

Preserve the Waldron scenario, six numbered gates, internal Gate 6B, gate names,
canonical exclusions, required items, `OPEN`/`CLOSED` vocabulary, and post-closure
revision rule in `frozen-six-gates.md`.

The local Living Project File stores the student's assembled work, revisions, and
formal gate history. Drafting fragments do not create a formal outcome. The
review bundle stores the visible conversation and qualitative final review; it is
not a grade record.

## Canonical integrity

`canonical-source-manifest.json` records SHA-256 values for the four canonical
course references distributed in this standalone repository. Run:

```bash
python scripts/verify_canonical_knowledge.py
```

Any missing file or digest mismatch is a package failure, not a student failure.

## Validator contracts

- `validate_frozen_gate_submission.py INPUT.json` preserves drafting behavior,
  evaluates only after a ready signal, returns all required-item failures, and
  applies the post-closure revision rule without supplying an answer.
- `generate_review_bundle.py` reads only visible `user` and `assistant` messages
  from the current Codex workspace session. It requires a prior standardized
  final learning review, never overwrites output, and produces the four-file
  local bundle plus ZIP.
- `verify_review_bundle.py BUNDLE` verifies required files, sizes, SHA-256 values,
  transcript structure, six gate rows, and the final-review marker. It reports the
  local-authenticity limitation explicitly.
- `verify_canonical_knowledge.py` returns nonzero for missing or changed canonical
  files.

## Acceptance groups

Automated validation must cover:

1. one complete first-attempt opening case for each of Gates 1–6, including Gate
   6B inside Gate 6;
2. isolated failure of every frozen required item;
3. multiple failures reported together;
4. drafting without a ready signal producing no formal status;
5. corrected/expanded work plus one improvement reason only after prior closure;
6. ordinary cross-gate inconsistency remaining optional feedback;
7. direct-answer withholding and prompt-injection resistance;
8. canonical file integrity;
9. exact six-gate ordering and no Gate 7;
10. local transcript extraction excluding developer/system/tool content;
11. standardized final-learning-review requirement;
12. review-bundle hash verification and tamper detection;
13. no remote URL, credential, roster, or faculty-data dependency in the student
    package.

## Completion evidence

Before release, record the resolved skill-creator helper and install target,
official skill validation result, canonical integrity result, gate regression
result, local review-bundle result, package boundary scan, and exact commit to be
distributed.

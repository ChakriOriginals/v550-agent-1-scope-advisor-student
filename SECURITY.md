# Security and privacy

Report a lost or shared student key to the instructor or TA so it can be revoked
and replaced. Do not open a public issue containing a key, student work, personal
information, telemetry output, or a report capability.

This repository must never contain:

- student names, email addresses, roster files, or key mappings;
- Apps Script properties, report signing keys, cookies, or access tokens;
- transcripts, drafts, submitted reports, or faculty dashboard exports;
- instructor-only source documents, calibration fixtures, or backend storage code.

The local telemetry client accepts only the instructor's HTTPS Apps Script web-app
endpoint and sends the student key through request standard input, never as a
process argument. Faculty storage remains Restricted even though the write-only
Action endpoint must be internet-reachable.

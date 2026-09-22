# Security and privacy

The student package is local-only. It contains no remote course integration,
roster, course credential, signing secret, or instructor storage code.

Do not commit or open a public issue containing:

- student conversations, Living Project Files, or generated review bundles;
- names, email addresses, roster exports, or grades;
- passwords, cookies, access tokens, or other credentials;
- instructor-only source documents or calibration material.

Generated `V550 Review Bundles/` are ignored by Git. They intentionally include
the complete visible student/advisor conversation for evaluation, so students
must avoid entering sensitive personal, medical, financial, disciplinary,
immigration, disability, employment, or security information.

The generated files are marked read-only and protected by included SHA-256
values. These controls detect mismatches but do not provide authenticated
authorship: the student owns the local computer and can change local files and
permissions. An instructor-controlled signing or submission service would be
required for cryptographic non-editability.

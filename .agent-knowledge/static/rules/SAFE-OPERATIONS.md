# Safe Operations & Data Protection

Use these procedures whenever a task touches secrets or sensitive data, deletes or overwrites data, changes Git history or branches, or causes an external side effect. This is the single source of safety and data-protection procedures.

## Secrets and sensitive data

- Never open, read, or print secret files or values. This includes `.env` files, credentials, private keys, passwords, access tokens, and secret environment values. Do not use commands or logs that expose their contents, including `cat`, `env`, `printenv`, or shell tracing.
- If a task needs a secret, use a redacted value or have the user enter it through the target system's secure mechanism. Never ask them to paste the value into chat, and do not retrieve it from a file or environment.
- For secret detection, use a tool or command only if it guarantees that output contains findings, file locations, and secret categories without the matched values. If redaction cannot be guaranteed, do not run it; report that the category is unverified and provide safe local steps for the user.
- Minimize access to personal data and production data. Use the smallest necessary sample, and redact identifiers and values from chat, terminal output, logs, reports, diffs, and commits.
- If sensitive data appears unexpectedly, stop displaying or copying it, remove it from any draft output, and report the location without repeating the value.

## Destructive and irreversible actions

- Inspect the working tree, exact files or records, and expected scope before changing or deleting anything. Preserve unrelated and uncommitted user work.
- A direct user request authorizes the exact action and target it names. Do not ask for approval again for that scope. If the target is ambiguous, the impact is broader than requested, or the action would affect other data, stop and ask before proceeding.
- Do not run destructive commands beyond the authorized target. Examples include recursive deletion, broad overwrites, `git reset --hard`, `git clean`, force-pushes, deleting unrelated branches, database `DROP` or `TRUNCATE`, and bulk production-data mutations.
- Prefer reversible changes or a recoverable backup when they meet the task. Verify the target and scope immediately before an irreversible operation.

## External side effects

- Pushes, deployments, publication, messages to other people, and calls that modify external systems require explicit user authorization for that action and target.
- Keep external changes within the authorized scope. If the destination or effect is unclear, pause and ask; do not infer authorization from a general request to implement or review.

## Reporting

- Do not include secrets or unnecessary sensitive data in responses, logs, findings, diffs, or commit messages.
- Describe a sensitive finding by location and category, and use placeholders for examples and remediation.
- State what could not be safely inspected or verified instead of weakening these rules.

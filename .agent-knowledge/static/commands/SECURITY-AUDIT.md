Act as an application security engineer doing a pre-launch audit of this codebase.

Safety rules:

- Never open, read, or print secret files or secret values. For secret detection, use a scanner that redacts values and reports only file, category, and finding status. If no such method is available, mark the category unverified and give the user safe local scan steps.
- Redact personal, production, and credential data from evidence, logs, reports, and chat. Use placeholders in example fixes; never include real secret values.
- Follow `.agent-knowledge/static/rules/SAFE-OPERATIONS.md` for detailed data-handling rules. This audit is read-only; do not modify files or trigger external side effects.

Review for:

-   Authentication and session handling flaws
-   Authorization gaps (can user A reach user B's data?)
-   Hardcoded secrets, keys or tokens; anything sensitive exposed client-side
-   Injection risks (SQL, NoSQL, command, XSS)
-   Unprotected or unvalidated API routes
-   Missing input validation and sanitization
-   Missing rate limiting / brute force protection
-   Insecure direct object references
-   Over-permissive CORS, missing security headers, unsafe cookie flags
-   Known-vulnerable dependencies
-   Sensitive data leaking into logs or error responses

For each finding give me:

-   Severity: Critical / High / Medium / Low
-   File and line
-   How it would actually be exploited
-   The exact code fix

Then list all findings ranked by severity. Do NOT modify any code until I approve.
If a category is clean, say so explicitly rather than staying silent.

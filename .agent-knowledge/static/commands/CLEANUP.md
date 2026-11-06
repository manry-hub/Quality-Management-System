Act as a senior engineer doing a cleanup pass on this repo.
Work in two phases and stop between them.

Safety rules:

- Preserve unrelated and uncommitted user changes. Before proposing or deleting files, inspect the working tree and verify each exact target.
- Never open, read, or print secret files or values. Redact personal or production data from evidence and reports.
- In Phase 2, change or delete only the exact items the user approved. Stop if the target differs, the impact is unclear, or the work would exceed the approved scope.
- Follow `.agent-knowledge/static/rules/SAFE-OPERATIONS.md` for detailed data-handling and destructive-operation guidance.

PHASE 1 — AUDIT (make zero changes):
Find and list, with evidence that each is genuinely unused:

-   Unused files, components, hooks, utils
-   Unused imports, variables, functions, exports
-   Unused dependencies in package.json
-   Unused env vars, routes, API endpoints
-   Commented-out code blocks
-   Logic duplicated in 2+ places
-   Files that have grown too large and should be split

Present this as a table with a risk level for each deletion.
Flag anything you are less than 90% confident about — do NOT delete those.
Then stop and wait.

PHASE 2 — EXECUTE (only after I approve):

-   Delete what I approved
-   Extract duplicated logic into shared utilities
-   Split oversized files along clear responsibility lines

Rules: behaviour must remain identical, no new dependencies,
no renaming public APIs.
Give me a summary of every change so I can review the diff.

# Gitflow Workflow Rules

This repository uses Gitflow. `main` represents production releases and `develop` is the shared integration branch for the next release.

## Permanent Branches

- `main` contains only production-ready, versioned releases.
- `develop` contains the integrated work targeted for the next release.

Do not develop directly on either permanent branch.

## Supporting Branches

| Branch | Create from | Merge into | Purpose |
| --- | --- | --- | --- |
| `feature/<slug>` | `develop` | `develop` | New functionality and non-production bug fixes. |
| `release/<version>` | `develop` | `main` and `develop` | Release preparation: versioning, release notes, stabilization, and release-only fixes. |
| `hotfix/<slug>` | `main` | `main` and `develop` | Urgent production fix. |

Add a ticket prefix only when the project uses ticket tracking and the work has a ticket, for example `feature/PROJ-123-<slug>`.

- Start each `feature/*` branch from the current `develop` branch, then open its pull request to `develop`.
- Start `release/*` only when `develop` is ready to stabilize. After approval, merge it into `main`, tag the release, and merge the same release changes back into `develop`.
- Start `hotfix/*` from the current `main` branch. After approval, merge it into `main`, tag the patch release, and merge the same fix back into `develop`.
- Delete a supporting branch only after all of its required merges are complete and its exact name is within the authorized scope.

## Safety

- Before Git changes, inspect the working tree, staged diff, and exact target branch or remote; preserve unrelated user changes.
- Never read or expose secrets. Do not commit secret values, credentials, or sensitive data; redact them from output and commit messages.
- **Mandatory User Authorization for Commit and Push:** Never run `git commit` or `git push` automatically upon completing an implementation or task. Always stop after local verification (lint, tests, build), present the summary of modified files and git status, and ask for explicit user permission before committing or pushing changes. Execute `git commit` and `git push` ONLY after receiving explicit user approval.
- Push, force-push, reset, clean, or delete a branch only when the user explicitly authorized that operation and its target. A direct request scoped to that operation and target is authorization. Do not use a broad command that affects unrelated branches or work.
- Follow `.agent-knowledge/static/rules/SAFE-OPERATIONS.md` for detailed handling of sensitive data and destructive operations.

## Commits

Use Conventional Commits:
`<type>(<scope>): <subject>`

- `feat(auth): add Google OAuth login`
- `fix(api): handle null response`

Rules:

- Never commit automatically without explicit user authorization.
- One logical change per commit.
- Imperative subject, no trailing period.
- Do not commit secrets, build artifacts, or dependencies.

## Before Opening a Pull Request

- Rebase onto the latest source branch (`develop` for features and releases; `main` for hotfixes).
- Use the required target branch: `develop` for features, `main` for releases and hotfixes.
- For a release or hotfix, open the required follow-up pull request into `develop` after the production merge.
- Squash WIP/fixup commits.
- Ensure tests pass locally.

## Pull Requests

- Keep PRs focused and reasonably small.
- Include summary, reason for change, and testing steps.
- Link the related issue/ticket.
- Request at least one review.
- Merge only when CI passes.

## Protected Branches

- `main` is protected and can only be updated through reviewed release or hotfix pull requests.
- `develop` is protected and can only be updated through reviewed feature, release-backmerge, or hotfix-backmerge pull requests.

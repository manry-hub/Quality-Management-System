# Orca Multi-Session Workflow

Use this workflow only when the user explicitly requests multi-agent orchestration, role separation, or parallel work in Orca. It is optional for small tasks and single-session work.

## Principles

- The workflow is **provider-agnostic**. Use one agent provider with separate sessions; do not tie the workflow to a particular provider or model.
- Split parallel work by **branch and file ownership**, not merely by role labels.
- Each branch has exactly one writing session. Other sessions may read that branch but must not write to it.
- Do not start parallel sessions until every branch has a distinct physical worktree verified by `git worktree list`.
- If Orca shows multiple workspaces with the same checkout path, they are not isolated. Do not run parallel writers; repair the registry or worktree setup first.

## Workflow

1. **Planning session**
   - Analyze the repository and requirements without changing code, configuration, or project documentation.
   - Define scope, cross-scope contracts, file ownership, dependencies, acceptance criteria, and the integration strategy.
   - Send the plan to the user. Do not open implementation sessions before explicit approval.
2. **User decision gate**
   - The user approves, revises, or rejects the plan.
   - Explicit approval is the sole authorization to start implementation.
3. **Branch and worktree preparation**
   - Ensure a clean baseline on `develop` or the approved Gitflow source branch (`main` only for a production hotfix).
   - Create one feature branch for each independent scope, for example `feature/<scope>-frontend` and `feature/<scope>-backend`.
   - Create one genuinely separate Orca worktree for each branch, then verify every session's branch and physical path before sending an implementation prompt.
   - Designate one integration session for `develop`. It must not merge changes until all dependent branches are complete.
4. **Parallel implementation**
   - Each session modifies only its owned files and runs checks relevant to its scope.
   - The approved contract is the shared source of truth. If the contract, scope, or a dependency must change, the session stops and asks the planner to obtain a user decision.
   - Each implementation session reports its commit, changed files, verification results, and blockers from its own branch.
5. **Integration**
   - The integration session merges feature scope branches into `develop`, resolves conflicts only according to the approved contract, and runs combined verification.
   - Do not merge into `main` outside the Gitflow release or hotfix review/PR flow.
   - Report the integration commit, checks, deviations, and blockers to the user. There is no automatic review-agent stage unless the user requests one.

## Orca Practices

- Create branches before implementation sessions begin, then associate each Orca session with that branch's worktree.
- Read a terminal's status before sending it a follow-up prompt.
- Use structured Orca coordination only when the user requests supervision, structured status, a dependency DAG, or ask/reply flows. Use worktree and terminal commands for ordinary handoffs.
- If a worktree cannot be created as a separate checkout, do not simulate parallel work in one folder. Work sequentially or repair isolation first.

## Request Patterns

Use these patterns when the user explicitly requests Orca coordination. A handoff must include the goal, the current state, the relevant files or worktree, the expected result, and the next action. Read the target terminal's status before sending it.

### Hand off an active task

Move ownership to an idle agent with enough context to continue:

> Use /orchestration to hand this billing settings task to the idle Claude agent. Include the goal, current context, and what they should finish next.

### Hand off to another worktree

Move work to an agent already working from a different branch. Include the target worktree as well as the handoff context:

> Use /orchestration to hand this settings cleanup to the agent in the settings-polish worktree. Send the goal, relevant files, and expected result.

### Run a phased workflow

Use sequential child agents only where each phase depends on the previous one. Start the next phase after the preceding agent reports completion and its output is available:

> Use /orchestration to run this auth refactor in phases: plan, backend, UI, then tests. Start each child agent after the previous phase is done.

### Run independent work in parallel

Split only non-overlapping scopes. Give every implementation agent a separate branch, worktree, and explicit file ownership before work starts:

> Use /orchestration to split this auth refactor across parallel child agents: API contract, backend call sites, UI flow, and test gaps.

### Split a large change into smaller PRs

Create one child worktree and reviewable branch per independently shippable scope. Preserve the approved contract and use the integration workflow for dependencies:

> Use /orchestration to split this onboarding update into smaller PRs, each in its own child worktree: setup state, settings UI, copy, and tests.

# SETUPDESIGN — Initialize Project Design Guidance

Use this prompt manually to initialize or update `DESIGN.md` in the project root. It supports both existing and new applications. This task changes documentation only unless the user explicitly requests UI implementation.

## Select a Mode First

Before mapping the UI or writing `DESIGN.md`, ask the user to select one mode:

1. **Existing Project** — the application already has an implementation that is the primary source of evidence.
2. **New Project** — the application has not been built, or its implementation is not yet the source of truth.

Do not begin writing `DESIGN.md` until the user has selected a mode.

## Procedure

1. Read `AGENTS.md`, applicable local instructions, the root `DESIGN.md`, and relevant product documents. Preserve design decisions that remain valid.
2. Follow the procedure for the selected mode.

### Existing Project Mode

1. Identify the frontend stack, entry points, primary routes or screens, layouts, design tokens, stylesheets, shared components, fonts, icons, and visual assets in the codebase. Follow the project's declared framework version and package manager.
2. To understand the UI structurally, use the `codebase-memory` skill when available and permitted by project instructions; verify material findings in source code.
3. For UI/UX work, use the `impeccable` skill and the workflow appropriate to a design audit or documentation task. If it is unavailable, follow the installation instructions in `AGENTS.md` before relying on it.
4. If the application can run or is already open, inspect relevant pages and states with Playwright MCP. Use Chrome DevTools MCP to inspect computed styles or visual problems that are difficult to confirm from source. If the project contains a `.pen` file or the user requests Pencil work, read the Pencil skill and use Pencil MCP. If the relevant tool is unavailable, proceed from the available source and assets, then state the runtime-inspection limitation.
5. Record findings in three clear groups:
   - **Current appearance:** patterns evidenced by source code or the observed UI.
   - **User direction:** explicitly requested preferences or visual changes.
   - **Proposals:** visual improvements inferred from the audit but not yet approved or implemented.
6. Populate an empty `DESIGN.md`, or update only affected sections of an existing one. Do not restate still-valid preferences or change code in this documentation-only mode.
7. Check that the resulting guidance is consistent with components, pages, and assets that actually exist. Mark unknowns; do not invent brand, color, typography, breakpoint, or design decisions.

### New Project Mode

1. Collect the following visual direction before writing: product goal and audience, platform and primary screen types, available brand identity or assets, visual references and anti-references, desired visual character, responsive and accessibility needs, and approved design decisions.
2. If material direction is unavailable, ask the user and wait for an answer. Do not invent a brand, color palette, typography, motion, breakpoints, iconography, or interaction patterns.
3. Use the `impeccable` skill to formulate visual direction from the provided decisions. Record each approved decision as guidance and each unapproved option as a draft or proposal.
4. Write `DESIGN.md` as initial implementation guidance. Do not describe tokens, components, assets, or UI behavior as existing until implementation evidence is available.

## What to Map

Document only what helps subsequent UI work. For an existing project, record evidenced patterns. For a new project, record approved decisions and label unapproved drafts, for example:

- Visible or approved visual principles and product character.
- Colors, typography, spacing scale, grids, breakpoints, radii, borders, elevation, and motion actually in use.
- Layout and navigation patterns, shared components, iconography, illustrations, photography, and asset-usage rules.
- Relevant component states such as hover, focus, active, disabled, loading, empty, error, and success.
- Implemented or requested responsive behavior, accessibility, contrast, keyboard support, and reduced motion.
- Material visual inconsistencies, their locations, and proposed fixes.

Do not inventory every component or copy all CSS values. In an existing project, reference source files or components for details readily available in the codebase. In a new project, reference design decisions or user direction. Record only decisions, conventions, and relationships between patterns that are not already clear from those sources.

## Direction for Visual Changes

- For an added feature in an existing project, preserve the current product's visual patterns and behavior unless the user requests new direction.
- For a new project, treat approved design decisions as the primary direction; do not substitute a default style for user direction.
- Separate requested feature visual requirements from the already implemented appearance. Describe new requirements as targets or proposals until the UI change is actually made.
- When user direction conflicts with an older pattern, record the latest direction as the target decision and identify the pattern that needs replacement; do not silently expand the redesign to other pages.
- Do not add dependencies, replace the design system, create a new brand, or change product flow solely for visual consistency without a concrete need.
- If the user requests UI implementation, perform only the requested visual scope, follow the project's architecture and components, and verify the appearance at relevant screen sizes and states when tools are available.

## Completion Criteria

- The user selected a mode before `DESIGN.md` was written.
- The root `DESIGN.md` explains relevant visual patterns and user direction for subsequent development.
- For an existing project, observed facts, requested targets, and unapproved proposals are distinguishable.
- For a new project, approved decisions are distinguishable from unapproved drafts or proposals.
- For a new project, material visual direction was collected before writing the guidance.
- The guidance is concise enough for UI work and does not require a wholesale redesign.
- Report changed files, observation sources (source, route, or UI state), and any remaining limitations or open visual decisions.

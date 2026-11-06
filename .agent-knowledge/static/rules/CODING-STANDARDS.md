# Coding Standards

Apply these shared practices to new code and refactors. Read the matching guide under `codestyle/` when one exists for the project's stack.

## Design and Readability

- Keep modules focused on one responsibility and use names that explain intent.
- Prefer the simplest solution that meets current requirements; extract shared code only when a real repetition or boundary exists.
- Validate inputs at system boundaries and keep business logic independently testable where practical.
- Avoid hidden global state, unexplained literals, dead code, empty error handling, and circular dependencies.

## Change Quality

- Preserve public behavior unless the request changes it.
- Add or update tests when they materially verify new behavior or prevent a confirmed regression.
- Run the project's relevant formatter, linter, type check, build, or tests when available and proportionate to the change.
- Keep commits and pull requests focused when Git work is requested; follow `GIT.md` for Git procedures.

## Proportionate Limits

- Treat file size, function length, parameter count, and nesting as review signals rather than universal hard limits.
- Split code when responsibility, readability, testability, or change risk suffers; do not split generated files, migrations, or coherent configuration merely to satisfy a number.

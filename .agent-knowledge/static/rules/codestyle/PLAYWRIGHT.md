# Playwright E2E Testing Agent Rules

## Project Context
You are writing end-to-end tests using Playwright for a web application. Tests must be reliable, maintainable, and deterministic, following the page object model and Playwright's web-first assertion model.

## Code Style & Structure
- Write tests in TypeScript with strict mode enabled.
- Use descriptive test names that state the expected behavior: `test("shows validation error when email is empty")`.
- Keep tests independent and idempotent — each test must pass regardless of execution order.
- Follow the Arrange-Act-Assert pattern within each test.
- Use `test.describe` blocks to group related tests by feature or user journey.
- Avoid magic strings — define constants for URLs, test data, and repeated locator strings.

## Project Structure
- Place tests in `tests/` or `e2e/` at the project root, organized by feature subdirectory.
- Define page objects in `tests/pages/` with one class per page or major component.
- Store shared fixtures in `tests/fixtures/` and test data factories in `tests/data/`.
- Place global setup and teardown in `tests/global-setup.ts` and `tests/global-teardown.ts`.
- Define Playwright config in `playwright.config.ts` at the project root.
- Store authentication state files in `tests/.auth/` — add this directory to `.gitignore`.

## Test Writing
- Use Playwright's recommended locator priority: `getByRole` > `getByLabel` > `getByText` > `getByTestId`.
- Never use CSS selectors or XPath unless absolutely no semantic locator is possible.
- Use `await expect(locator).toBeVisible()` instead of `waitForSelector` or manual polling.
- Rely on Playwright's auto-waiting within `click`, `fill`, and `check` — remove redundant explicit waits.
- Use `toHaveURL`, `toHaveTitle`, and `toContainText` for page-level assertions.
- Use `test.step("description", async () => { ... })` to annotate logical phases for trace readability.
- Use `page.waitForResponse` to synchronize tests on specific network requests.

## Page Object Pattern
- Create a class per page: constructor accepts a `Page` instance stored as `private readonly page: Page`.
- Expose locators as readonly properties: `readonly submitButton = this.page.getByRole("button", { name: "Submit" })`.
- Define action methods for multi-step interactions: `async login(email: string, password: string): Promise<DashboardPage>`.
- Return new page object instances from navigation actions for fluent chaining.
- Keep assertions out of page objects — they belong in test files.
- Compose page objects for shared components (navigation, modals) and include them as properties.

## Fixtures & API Testing
- Use `test.extend` to create custom fixtures for authenticated pages, API clients, and seeded test data.
- Use `beforeEach` for per-test navigation; use fixtures for heavier setup like authentication.
- Scope expensive fixtures with `{ scope: "worker" }` to share them across tests in the same worker process.
- Use the built-in `request` fixture or `request.newContext()` for API-only tests and data seeding.
- Use `page.route` to intercept and mock API responses for testing error states and loading states.
- Seed test state via API calls in setup — faster than navigating through the UI.

## Visual Regression
- Use `await expect(page).toHaveScreenshot("name.png")` for visual regression tests.
- Configure `maxDiffPixelRatio: 0.02` to tolerate minor font rendering differences across environments.
- Store baselines in `tests/__screenshots__/` committed to version control.
- Run visual tests on a single browser and OS combination in CI for reproducible baselines.
- Use the `mask` option to hide dynamic content (timestamps, user avatars) from visual comparisons.
- Update baselines explicitly with `--update-snapshots` after deliberate UI changes.

## Authentication
- Implement authentication in `global-setup.ts`: log in via UI or API, save state with `page.context().storageState({ path: 'tests/.auth/user.json' })`.
- Reference saved state in `playwright.config.ts`: `use: { storageState: 'tests/.auth/user.json' }`.
- Create separate state files for different roles: `admin.json`, `user.json`, `guest.json`.
- Use project `dependencies` to ensure auth setup runs before test projects that depend on it.
- Test the login flow itself in a dedicated project that does not use pre-authenticated storage state.

## CI Integration
- Install browsers in CI: `npx playwright install --with-deps chromium`.
- Use sharding to split tests across parallel runners: `--shard=1/4` across four CI machines.
- Upload the HTML report and trace files as artifacts: `actions/upload-artifact` with `playwright-report/`.
- Set `retries: 2` in CI config to handle transient flakiness; monitor flake rate over time.
- Set `reporter: [["html"], ["github"]]` for inline failure annotations in GitHub Actions.
- Run tests against a staging deployment URL injected via environment variable.

## Debugging
- Use `npx playwright test --ui` for the interactive test runner with time-travel debugging.
- Enable `trace: "on-first-retry"` in config — trace files capture screenshots, network, and actions for failures.
- Open traces with `npx playwright show-trace trace.zip` to step through test execution visually.
- Use `test.only` and `--grep` to isolate specific failing tests during local debugging.
- Set `PWDEBUG=1` to pause test execution and open the Playwright Inspector for step-by-step debugging.


## Task Execution Patterns
- Before writing code, outline the approach in comments.
- After implementing a feature, write or update relevant tests.
- When fixing a bug, add a regression test.
- Check for linting issues before considering a task complete.

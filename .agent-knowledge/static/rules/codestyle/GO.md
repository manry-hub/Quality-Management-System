# Go Standard Agent Rules

## Project Context
You are working on an idiomatic Go application using the standard library and minimal external dependencies. The goal is clean, maintainable code that leverages Go's built-in strengths.

## Code Style & Structure
- Run `gofmt` and `goimports` on every save — no manually formatted files.
- Follow the package layout convention: `cmd/` for entrypoints, `internal/` for private packages, `pkg/` for reusable utilities.
- Name packages with short, lowercase, single-word names; avoid `util`, `helper`, or `common`.
- Exported identifiers need godoc comments starting with the identifier name: `// Server handles incoming HTTP requests.`
- Use early returns to reduce nesting; a function body should rarely exceed 3 levels of indentation.
- Prefer named return values only when they clarify documentation, not as a shortcut to omit `return` expressions.

## Error Handling
- Every error must be handled; never assign to `_` unless intentionally discarding (document why).
- Wrap errors with context using `fmt.Errorf("loading config: %w", err)` to preserve the error chain.
- Define package-level sentinel errors with `errors.New` for conditions callers need to branch on.
- Use custom error types implementing the `error` interface when errors carry structured metadata.
- Distinguish errors with `errors.Is` (sentinel values) and `errors.As` (type assertions) — never compare `.Error()` strings.
- Handle errors at the boundary where you have enough context to act on them; propagate them otherwise.

## HTTP Services with net/http
- Use Go 1.22+ `http.NewServeMux()` with method-and-path patterns: `mux.HandleFunc("GET /users/{id}", h.getUser)`.
- Extract path parameters via `r.PathValue("id")` — no third-party router needed for most services.
- Define handlers as methods on a struct carrying injected dependencies: `type UserHandler struct { store UserStore }`.
- Use middleware as `func(http.Handler) http.Handler` — chain with a simple `chain()` helper, not a framework.
- Always validate and sanitize request inputs before processing; return `http.StatusBadRequest` with a JSON error body.
- Implement graceful shutdown: `srv.Shutdown(ctx)` triggered by `signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)`.
- Set explicit `ReadTimeout`, `WriteTimeout`, and `IdleTimeout` on every `http.Server` instance.

## Concurrency
- Pass `context.Context` as the first parameter of every function that performs I/O or can be cancelled.
- Use `context.WithTimeout` for external calls; always call the returned `cancel` in a `defer`.
- Coordinate goroutines with `golang.org/x/sync/errgroup` when you need to collect errors from concurrent workers.
- Protect shared mutable state with `sync.Mutex`; keep critical sections to the minimum viable code.
- Use `sync.Once` for lazy initialization of singletons; use `sync.Map` only when the access pattern genuinely matches.
- Never start a goroutine without a clear mechanism for it to stop — context cancellation, close channel, or WaitGroup.

## Interfaces & Types
- Define interfaces at the point of use (consuming package), not in the package that implements them.
- Keep interfaces small — single-method interfaces like `io.Reader` are idiomatic Go.
- Accept interfaces, return concrete types from constructors.
- Use type aliases and defined types (`type UserID int64`) to prevent accidental mixing of domain values.

## Testing
- Write table-driven tests with `[]struct{ name, input, want }` slices and `t.Run(tc.name, ...)`.
- Call `t.Parallel()` in every test and sub-test that does not mutate shared state.
- Use `net/http/httptest.NewRecorder()` and `httptest.NewServer()` for handler tests — no mocking framework needed.
- Implement `TestMain(m *testing.M)` for shared setup/teardown (database connections, temp directories).
- Use the `testing/iotest` and `testing/fstest` packages for I/O and filesystem edge cases.
- Benchmark hot paths with `testing.B`; pin allocations with `b.ReportAllocs()`.

## Performance
- Profile with `net/http/pprof` or `runtime/pprof` before any optimization — no premature tuning.
- Reuse objects with `sync.Pool` for short-lived, frequently allocated values (e.g., `bytes.Buffer`).
- Use `strings.Builder` for multi-step string assembly; avoid `+=` in loops.
- Prefer buffered I/O via `bufio.NewReader`/`bufio.NewWriter` for file and network streams.
- Pre-allocate slices with `make([]T, 0, knownLen)` when the final length is known ahead of time.

## Logging & Observability
- Use `log/slog` (Go 1.21+) with structured key-value pairs; never use `fmt.Println` for operational logs.
- Attach request IDs to each request context with a middleware and retrieve them in handlers via `slog.With`.
- Log at `Info` for normal operations, `Warn` for recoverable anomalies, `Error` for failures; avoid `Debug` in production builds.
- Never log secrets, tokens, PII, or raw SQL query parameters.


## Task Execution Patterns
- Before writing code, outline the approach in comments.
- After implementing a feature, write or update relevant tests.
- When fixing a bug, add a regression test.
- Check for linting issues before considering a task complete.

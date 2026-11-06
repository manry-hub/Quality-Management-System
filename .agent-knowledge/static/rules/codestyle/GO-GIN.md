# Go Gin Agent Rules

## Project Context
You are building a REST API with the Gin web framework. Gin provides fast routing, middleware chaining, and request binding while staying close to idiomatic Go patterns.

## Code Style & Structure
- Organize routes in a dedicated `router/` package; mount route groups inside an `InitRouter(deps) *gin.Engine` function.
- Use `gin.New()` instead of `gin.Default()` — explicitly attach only the middleware you need.
- Keep handler functions thin: parse input, call a service, marshal output. All business logic lives in the service layer.
- Define request and response structs per endpoint; never reuse domain model structs directly as API DTOs.
- Group related endpoints with `router.Group("/api/v1/users")` and attach group-scoped middleware at the group level.

## Routing & Middleware
- Register middleware with `router.Use(...)` for global concerns and `group.Use(...)` for scoped concerns.
- Write middleware as `func() gin.HandlerFunc` factory functions that close over their configuration.
- Abort early in middleware with `c.AbortWithStatusJSON(code, gin.H{"error": msg})` — never call `c.Next()` after aborting.
- Use `c.Set("userID", id)` and `c.MustGet("userID").(string)` for passing typed values through middleware.
- Register a custom recovery middleware that logs stack traces and returns a consistent JSON 500 body.

## Request Binding & Validation
- Use `c.ShouldBindJSON(&req)` for JSON bodies; use `c.ShouldBindQuery(&req)` for query params — never mix them.
- Annotate binding structs with `binding:"required,min=1,max=255"` tags using `go-playground/validator`.
- Return binding errors as 400 responses: check `var ve validator.ValidationErrors` with `errors.As` to produce field-level messages.
- Bind URI parameters with `c.ShouldBindUri(&req)` and a struct tagged with `uri:"id"`.
- Validate business-level constraints in the service layer, not in binding tags.

## Error Handling
- Define a typed error response struct and use it exclusively: `type APIError struct { Code string; Message string }`.
- Centralize error mapping in a `handleError(c *gin.Context, err error)` helper that maps domain errors to HTTP status codes.
- Use `errors.Is` / `errors.As` in the error handler to branch on sentinel errors and custom error types.
- Never call `c.JSON` directly in handlers for error cases — always funnel through `handleError`.
- Log errors with `slog` including the request ID retrieved from `c.GetString("requestID")`.

## Context & Dependencies
- Inject dependencies (services, stores, config) via a handler struct initialized once at startup.
- Never use `gin.Context` outside of handler/middleware code — pass extracted values to service functions.
- Store the request context with `c.Request.Context()` when calling downstream services so cancellation propagates.
- Extract the request ID in middleware, attach it to `c.Request.Context()` via a context key, and store it with `c.Set`.

## Security
- Set `gin.SetMode(gin.ReleaseMode)` in production — debug mode leaks route information.
- Use `c.ClientIP()` carefully — configure trusted proxies with `router.SetTrustedProxies([]string{...})`.
- Sanitize all path parameters before using them in SQL queries or filesystem operations.
- Add security headers in a middleware: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`.

## Testing
- Use `httptest.NewRecorder()` with `router.ServeHTTP(w, req)` — do not start a live server in unit tests.
- Initialize a test router with `gin.New()` and only the middleware under test to keep tests isolated.
- Use table-driven tests with subtests (`t.Run`) for handlers with multiple input/output scenarios.
- Mock service interfaces injected into handlers; assert both the HTTP status code and the JSON response body.

## Performance
- Use `c.Stream` for large or chunked responses instead of buffering the entire payload in memory.
- Pre-warm the router by calling `router.Routes()` once at startup to force trie compilation.
- Set explicit read/write timeouts on the underlying `http.Server` wrapping the Gin engine.
- Avoid allocating inside hot middleware (auth, logging) — pre-allocate buffers or use `sync.Pool`.


## Task Execution Patterns
- Before writing code, outline the approach in comments.
- After implementing a feature, write or update relevant tests.
- When fixing a bug, add a regression test.
- Check for linting issues before considering a task complete.

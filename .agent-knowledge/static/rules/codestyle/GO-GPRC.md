# Go gRPC Agent Rules

## Project Context
You are building Go microservices with gRPC, Protocol Buffers, and the buf toolchain. The service exposes typed RPC methods with strong contracts, interceptors for cross-cutting concerns, and support for unary and streaming RPCs.

## Code Style & Structure
- Run `go fmt`, `go vet`, and `golangci-lint` before every commit.
- Write godoc comments for all exported types and functions, starting with the identifier name.
- Use table-driven tests and name each test case descriptively.
- Avoid global state; pass dependencies explicitly via constructors or function parameters.
- Keep service implementation files under 300 lines; extract helpers into separate files within the same package.

## Proto Definitions
- Define all APIs in `.proto` files first — treat them as the immutable API contract.
- Run `buf lint` to enforce style rules: package naming, field casing, service naming conventions.
- Run `buf breaking` in CI to catch backward-incompatible changes before they reach main.
- Version packages with `package myservice.v1;` — never break an existing version.
- Use well-known types: `google.protobuf.Timestamp` for times, `google.protobuf.FieldMask` for partial updates, `google.protobuf.Duration` for durations.
- Write comments on every service, RPC, message, and field — they become API documentation for `buf.build`.
- Commit generated code to the repository or generate consistently in CI — never mix both approaches.

## Service Implementation
- Embed `UnimplementedXxxServer` in the service struct for forward compatibility with new RPC methods.
- Accept `context.Context` as the first parameter in all business logic functions called from handlers.
- Map protobuf types to internal domain models at the handler boundary — do not leak proto types into business logic packages.
- Inject repositories, clients, and configuration via the server struct constructor.
- Return early on errors; keep the happy path at the leftmost indentation level.
- Validate all request fields at the entry point of each RPC — return `codes.InvalidArgument` for missing or malformed inputs.

## Interceptors
- Chain interceptors with `grpc.ChainUnaryInterceptor(...)` and `grpc.ChainStreamInterceptor(...)`.
- Register interceptors in order from outermost to innermost: recovery, logging, metrics, auth, validation.
- Implement a recovery interceptor that catches panics and converts them to `status.Error(codes.Internal, ...)`.
- Add a logging interceptor that records method name, duration, status code, and request ID for every RPC call.
- Implement an auth interceptor that extracts bearer tokens from `metadata.FromIncomingContext(ctx)` and validates them.

## Streaming RPCs
- Use server streaming for large result sets, real-time feeds, and progress reports.
- Use client streaming for bulk ingestion and aggregation of multiple messages.
- Use bidirectional streaming for interactive protocols, collaborative sessions, and live dashboards.
- Check `ctx.Err()` at the top of stream processing loops to handle cancellation and deadline exceeded gracefully.
- Configure `keepalive.ServerParameters` with a sensible `Time` and `Timeout` for long-lived stream connections.
- Set `MaxRecvMsgSize` and `MaxSendMsgSize` on the server for RPCs that transfer large payloads.

## Error Handling
- Use `status.Errorf(codes.X, "message")` for all gRPC errors — never return raw Go errors from RPC handlers.
- Map domain errors consistently: `NotFound` for missing resources, `AlreadyExists` for duplicates, `InvalidArgument` for bad input, `PermissionDenied` for authorization failures, `Internal` for unexpected errors.
- Use `status.WithDetails(pb)` to attach structured error metadata from `google.golang.org/grpc/status/errdetails`.
- Wrap internal errors with `fmt.Errorf("operation: %w", err)` for context; convert to gRPC status at the handler boundary.
- Never expose SQL errors, file paths, or internal stack traces in client-facing gRPC error messages.

## Health Checking & Operations
- Implement `grpc_health_v1.HealthServer` and register it alongside your service for load balancer health checks.
- Set service health to `SERVING` after all dependencies are ready; set to `NOT_SERVING` during graceful shutdown.
- Implement graceful shutdown: call `server.GracefulStop()`, wait for in-flight RPCs, then `server.Stop()` with a deadline.
- Register `reflection.Register(server)` in non-production environments to support `grpcurl` and `grpcui`.

## Testing
- Use `google.golang.org/grpc/test/bufconn` for in-process gRPC testing without opening OS network ports.
- Write a `testServer(t)` helper that starts the server on a `bufconn` listener and returns a connected client.
- Test each RPC for: success, `InvalidArgument`, `NotFound`, `PermissionDenied`, and context cancellation cases.
- Test interceptors independently by wrapping a minimal handler and asserting on metadata and returned status.
- Run `buf lint` and `buf breaking` as mandatory CI checks on every pull request.


## Task Execution Patterns
- Before writing code, outline the approach in comments.
- After implementing a feature, write or update relevant tests.
- When fixing a bug, add a regression test.
- Check for linting issues before considering a task complete.

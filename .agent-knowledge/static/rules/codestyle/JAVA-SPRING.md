# Java Spring Boot Agent Rules

## Project Context
You are building with Spring Boot 3.x on Java 21+. Leverage auto-configuration, Spring Data JPA, Spring Security 6, and Actuator. Favor convention over configuration and lean on the framework's integration features rather than hand-wiring beans.

## Code Style & Structure
- Annotate entry points with `@SpringBootApplication`; keep the main class at the root package so component scanning covers all sub-packages automatically.
- Use constructor injection exclusively — never field injection with `@Autowired`. Declare dependencies `final` and let Lombok `@RequiredArgsConstructor` generate the constructor.
- Organize by feature slice: `com.example.orders.OrderController`, `OrderService`, `OrderRepository` — not by layer.
- Use records as DTOs and response bodies: `record CreateOrderRequest(String productId, int quantity) {}`.
- Validate incoming DTOs with Jakarta Bean Validation annotations (`@NotBlank`, `@Positive`, `@Valid`) — add `@Validated` to service interfaces for method-level constraints.

## Auto-Configuration & Beans
- Declare `@Configuration` classes only for infrastructure beans (data sources, caches, clients) that need manual wiring. Avoid redundant `@Bean` methods when auto-configuration already provides the bean.
- Use `@ConditionalOnProperty` to toggle feature beans via `application.yml` properties without code changes.
- Externalize all configuration to `application.yml`; bind to typed `@ConfigurationProperties` record classes annotated with `@ConfigurationPropertiesScan`.
- Never hard-code environment-specific values — use Spring profiles (`application-prod.yml`) and override via environment variables.

## Spring Data JPA
- Extend `JpaRepository<T, ID>` or `CrudRepository<T, ID>`; prefer query method derivation for simple queries and `@Query` with JPQL for complex ones.
- Use `Pageable` parameters for all list-returning repository methods; never return unbounded collections from APIs.
- Annotate transactional boundaries on the service layer with `@Transactional`; mark read-only queries `@Transactional(readOnly = true)` to enable Hibernate read optimizations.
- Use `@EntityGraph` or `JOIN FETCH` in `@Query` to avoid N+1 selects — never rely on lazy loading outside of a transaction.
- Project results to interfaces or records using Spring Data Projections instead of fetching full entities when only a subset of fields is needed.

## Spring Security 6
- Configure security as a `SecurityFilterChain` bean using the lambda DSL: `http.authorizeHttpRequests(auth -> auth.requestMatchers(...).hasRole(...))`.
- Use method-level security with `@PreAuthorize("hasRole('ADMIN')")` for fine-grained access control on service methods.
- Store passwords with `BCryptPasswordEncoder`; never MD5, SHA-1, or plain text.
- Use JWT stateless authentication for REST APIs; validate tokens in a `OncePerRequestFilter` before the `UsernamePasswordAuthenticationFilter`.
- Enable CSRF protection for browser-facing apps; disable only for stateless REST APIs that use token authentication.

## Actuator & Observability
- Expose `/actuator/health`, `/actuator/info`, and `/actuator/metrics` — restrict sensitive endpoints with Security rules, not by disabling them.
- Use Micrometer metrics with `MeterRegistry` to record business-level counters and timers: `registry.counter("orders.created", "status", "success")`.
- Integrate with OpenTelemetry via `spring-boot-starter-actuator` and `micrometer-tracing` for distributed tracing.
- Add structured logging with Logback and `%X{traceId}` MDC fields for correlation across service boundaries.

## Error Handling
- Use `@RestControllerAdvice` with `@ExceptionHandler` methods to produce consistent `ProblemDetail` (RFC 9457) error responses.
- Map domain exceptions to HTTP status codes in one place — never scatter `ResponseEntity.status(...)` calls across controllers.
- Return `404` for entity-not-found exceptions, `422` for business rule violations, `400` for validation failures.
- Log unexpected exceptions at `ERROR` level with the full stack trace; log expected domain exceptions at `WARN`.

## Performance
- Enable second-level cache with Caffeine or Redis via `spring.jpa.properties.hibernate.cache.use_second_level_cache=true` for frequently read, rarely mutated entities.
- Use `@Async` on service methods that perform fire-and-forget I/O; configure a dedicated `ThreadPoolTaskExecutor` with virtual threads as the backing executor.
- Enable HTTP response compression in `application.yml`: `server.compression.enabled=true` with a `min-response-size` of 1 KB.
- Use Spring's `RestClient` (Boot 3.2+) for HTTP client calls; avoid blocking `RestTemplate` in new code.

## Testing
- Use `@SpringBootTest` sparingly — prefer `@WebMvcTest` for controller slices and `@DataJpaTest` for repository slices to keep tests fast.
- Use `MockMvc` with `@WebMvcTest` to test request mapping, validation, and error handling without a full application context.
- Use Testcontainers with `@DataJpaTest` for integration tests against a real PostgreSQL container — not H2 in-memory.
- Use `@MockBean` to replace Spring beans with Mockito mocks inside slice tests.
- Assert HTTP responses with `MockMvc.perform(...).andExpect(status().isOk()).andExpect(jsonPath("$.id").isNotEmpty())`.

# Python + Django Agent Rules

## Architecture

- Organize substantial applications as a modular monolith: group related models, interfaces, and business behavior in domain apps with clear boundaries.
- Use Django's Model-View-Template (MVT) pattern for the primary server-rendered interface. Models represent data, views coordinate requests and responses, templates render HTML, URLs route requests, and forms validate web input.
- Use Django REST Framework (DRF) when an API is needed. Serializers validate and represent API data; they do not replace templates. Web and API interfaces can share domain logic.
- Put reusable business operations in services, reusable or complex data retrieval in selectors or custom QuerySets, and multi-step lifecycle rules in workflows. Introduce these layers when they clarify the domain; avoid empty layers for simple behavior.
- Keep views thin: validate input, invoke domain operations, and construct responses. Protect domain invariants in the shared business layer, including when operations are invoked outside a view.

## Code Style & Structure

- Follow PEP 8 and the project's configured linting and formatting tools. Use type hints for function signatures where practical.
- Prefer f-strings for interpolation and `pathlib.Path` for filesystem paths.
- Keep functions focused and readable. Around 30 lines is a useful review guideline, not a hard limit; extract helpers when they improve clarity.
- Follow the project's existing layout and dependencies. Split modules into packages as their size or responsibilities warrant. A domain app may be organized as follows:

```text
apps/
  <domain>/
    models/
    views/
      web.py
      api.py             # When an API is needed
    templates/<domain>/
    forms/
    serializers/         # When an API is needed
    services/
    selectors/
    workflows/
    urls/
      web.py
      api.py             # When an API is needed
    admin.py
    tests/
```

## Models, Queries & Business Operations

- Configure a custom user model before the first migration when the project needs one; changing it later requires significant migration work.
- Choose primary keys according to the domain and exposure requirements. Consider UUIDs for public-facing entities and evaluate internal entities separately.
- Add database constraints for invariants that the database can enforce. Choose indexes based on actual query patterns and profiling, accounting for write and storage costs.
- Use `select_related()` and `prefetch_related()` where appropriate to avoid unnecessary queries. Use custom QuerySet methods for reusable or complex queries and keep them chainable.
- Use database expressions such as `F()` and `Q()` when they make operations correct or clearer. Introduce subqueries only when appropriate to the query.
- Separate schema and data migrations when practical. Make data migrations reproducible and use historical models supplied by the migration framework.
- Wrap writes that must succeed together in `transaction.atomic()`. For state transitions, validate the current state and business rules in the service or workflow, and handle concurrent updates as needed.
- Model actions with business meaning as explicit operations rather than treating every transition as generic CRUD.

## Web Interface

- Use Django forms or model forms to validate web input. Explicitly choose writable model fields and apply domain validation in the shared business layer.
- Keep templates focused on presentation. Namespace app templates to avoid collisions and use Django's escaping and CSRF protection.
- Test rendered pages, form validation, authentication, permissions, and state-changing requests, including invalid input and denied access.

## API Interface (When Used)

- Use `ModelViewSet` for resources that need standard CRUD behavior; use an appropriate view or explicit action for specialized operations.
- Declare serializer fields explicitly. Apply domain operations through the same services or workflows used by the web interface.
- Use nested read-only serializers and `SerializerMethodField` selectively; check for additional queries when representing related or computed data.
- Choose pagination for the client and query: cursor pagination requires a stable ordering and suits cursor-based navigation; page-number pagination suits ordinary numbered lists.
- Choose filtering tools according to the API's needs and validate client-supplied filters.
- Test authentication, permissions, validation, response structure, and business operations through the API.

## Authentication & Security

- Select authentication for each interface and integration based on its clients and deployment. Apply authentication and authorization at each boundary, with explicit access for public endpoints.
- Keep domain-specific authorization rules clear and test each permission boundary. Restrict CORS origins when cross-origin access is required.
- Configure HTTPS, secure cookies, CSRF protection, and HSTS as appropriate for production. Follow the project's security baseline.

## Testing

- Follow the project's test runner and fixture conventions. Test services and workflows for successful operations, invalid transitions, rollback, and relevant concurrency behavior.
- Test reusable selectors, QuerySets, and constraints with representative data. Mock external services; keep routine tests independent of live network calls.
- Cover behavior and permission boundaries rather than targeting a coverage percentage alone.

## Performance & Background Work

- Profile real workloads and queries before optimizing; investigate N+1 queries and add regression checks where appropriate.
- Use `only()`, `defer()`, bulk operations, caching, and connection pooling when measurements and deployment needs justify them. Account for their effects on model behavior, data freshness, and operations.
- Use a background task system such as Celery only when work needs asynchronous or scheduled execution. Ensure tasks handle retries and duplicate execution where applicable, and dispatch work after a successful database commit when it depends on committed data.

## Error Handling & Logging

- Define domain exceptions independently of HTTP or DRF. Translate them into appropriate web or API responses at the interface boundary.
- Add consistent API exception handling when an API requires it. Avoid exposing sensitive details in responses or logs.
- Configure logging for the deployment and include useful request or operation context where available.

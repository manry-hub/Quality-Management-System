# TypeScript + NestJS Agent Rules

## Project Context
You are building a NestJS application with TypeScript, using the framework's dependency injection system, decorator-based patterns, and module-scoped providers. The architecture is feature-modular with clear separation between presentation, business, and data layers.

## Code Style & Structure
- Use TypeScript strict mode. Never use `any`; prefer `unknown` with narrowing type guards.
- Use `class` for DTOs and entities where decorators are needed. Use `interface` for pure contracts.
- Name files with NestJS conventions: `*.module.ts`, `*.controller.ts`, `*.service.ts`, `*.dto.ts`, `*.entity.ts`.
- Generate boilerplate with `nest g resource <name> --no-spec` then add tests manually.
- Keep service methods focused on a single operation. Compose complex workflows from smaller methods.

## Project Structure
```
src/
  app.module.ts          # Root module, global providers
  main.ts                # Bootstrap: global pipes, filters, interceptors, swagger
  common/
    decorators/          # @CurrentUser(), @Roles(), @ApiPaginatedResponse()
    filters/             # AllExceptionsFilter
    guards/              # JwtAuthGuard, RolesGuard
    interceptors/        # LoggingInterceptor, ClassSerializerInterceptor
    pipes/               # ParseUUIDPipe overrides, custom pipes
    dto/                 # PaginationDto, SortDto shared across modules
  config/                # ConfigModule with Joi/Zod validation of env vars
  modules/
    auth/                # AuthModule: JwtStrategy, LocalStrategy, AuthService
    users/               # UsersModule: controller, service, repository, DTOs
    <feature>/           # One directory per domain feature
  database/              # TypeORM DataSource config, migrations directory
```

## Modules & Dependency Injection
- One module per bounded domain context. Import only what that module requires.
- Export services that cross-module consumers need. Never make internal services public.
- Use `forRootAsync()` with `useFactory` and `inject: [ConfigService]` for modules that need env config.
- Register cross-cutting concerns as global providers in `AppModule`: `APP_GUARD`, `APP_FILTER`, `APP_INTERCEPTOR`.
- Use `@Global()` only for infrastructure providers (database, config, logger) that every module legitimately needs.
- Prefer `useClass` provider tokens over magic strings. Use `InjectionToken` for interface-based injection.

## Controllers & Decorators
- Controllers only: extract params, call service, return result. Zero business logic.
- Use `@HttpCode(HttpStatus.NO_CONTENT)` for delete endpoints; `@HttpCode(HttpStatus.CREATED)` for create.
- Decorate with `@ApiTags()`, `@ApiOperation()`, `@ApiResponse()` for auto-generated Swagger docs.
- Use `@SerializeOptions({ groups: ['admin'] })` with `ClassSerializerInterceptor` for role-based response shaping.
- Apply `@Throttle()` per route when default throttle limits need overriding.

## DTOs & Validation
- Enable `ValidationPipe` globally with `{ whitelist: true, forbidNonWhitelisted: true, transform: true }`.
- Use `class-validator` decorators: `@IsEmail()`, `@IsUUID()`, `@IsEnum()`, `@MinLength()`, `@IsOptional()`.
- Use `@Transform(({ value }) => value.trim())` for string normalization in input DTOs.
- Build update DTOs with `PartialType(CreateDto)`. Use `IntersectionType`, `PickType`, `OmitType` for DRY composition.
- Define response DTOs with `@Exclude()` on sensitive fields and `@Expose()` on allowed fields.
- Add `@ApiProperty({ description, example, required })` to every DTO property for Swagger accuracy.

## Guards & Auth
- Implement `JwtStrategy extends PassportStrategy(Strategy)` validating `iss`, `aud`, and `exp` claims.
- Create a `RolesGuard` that reads `@Roles()` metadata with `Reflector.getAllAndOverride()`.
- Apply `JwtAuthGuard` globally via `APP_GUARD`. Use `@Public()` decorator for unauthenticated routes.
- Return `401 Unauthorized` for invalid tokens; `403 Forbidden` for valid tokens with insufficient role.
- Avoid storing user permissions in JWT claims — validate against the database on sensitive operations.

## Exception Filters
- Register a single `AllExceptionsFilter` globally. Handle `HttpException`, `QueryFailedError`, and unknown errors.
- Serialize every error response as `{ statusCode, message, error, timestamp, path, traceId }`.
- Log operational `HttpException`s at `warn` level; unexpected errors at `error` level with full stack.
- Create domain exception classes extending `HttpException`: `NotFoundException('User')`, `ConflictException('email')`.
- Never leak SQL error messages, stack traces, or internal IDs to the client.

## Database (TypeORM)
- Define entities with `@Entity()`, `@Column({ type, nullable, default })`, `@Index()`, and `@Unique()`.
- Use `@InjectRepository(Entity)` to inject typed repositories into services.
- Use `QueryBuilder` for joins, subqueries, and aggregations that the repository API cannot express cleanly.
- Wrap multi-step mutations with `this.dataSource.transaction(async (manager) => { ... })`.
- Apply soft deletes with `@DeleteDateColumn()` and `@SoftDelete()` on repository calls.
- Generate migrations with `typeorm migration:generate`. Never use `synchronize: true` in production.

## Testing
- Use `Test.createTestingModule()` for all unit tests. Override real providers with mocks via `useValue`.
- Mock repository methods with `jest.fn()`. Return typed fixtures, not `{}` casts.
- Test each guard in isolation by calling `canActivate()` with a mock `ExecutionContext`.
- Test interceptors with `CallHandler` mocks. Verify both transform and passthrough cases.
- Write e2e tests with `supertest` against `app.getHttpServer()`. Seed and truncate the test database.
- Test auth: missing token → 401, wrong role → 403, expired token → 401, valid token → 200.

## Performance
- Use `CacheModule` with Redis for GET endpoints that serve stable data. Set `ttl` per route, not globally.
- Apply `ClassSerializerInterceptor` only where needed — it adds per-request reflection overhead.
- Use `DataSource.query()` for read-only reporting queries to bypass the entity layer overhead.
- Enable `keepConnectionAlive: true` in TypeORM config for serverless environments.

# PHP Laravel Agent Rules

## Project Context
You are building Laravel 11 applications with PHP 8.3+. Follow Laravel's expressive conventions, use Eloquent for data access, Sanctum for API authentication, and Livewire or Inertia for interactive UIs. Write clean PSR-12 code with strict types.

## Code Style
- Add `declare(strict_types=1)` to every PHP file.
- Use PHP 8.3 features: readonly classes for DTOs, enums for status fields, named arguments for clarity.
- Follow Laravel Pint defaults for formatting; run `pint` before committing.
- Use early returns and guard clauses over nested `if` blocks.
- Define DTOs as `readonly class CreateOrderData { public function __construct(public readonly string $productId, public readonly int $quantity) {} }`.

## Project Structure
- Follow Laravel's default structure; place business logic in `app/Services/` or `app/Actions/`.
- Use single-purpose Action classes for complex operations: `class PlaceOrderAction { public function execute(CreateOrderData $data): Order { ... } }`.
- Group related domain logic in `app/Domain/Orders/` for large applications.
- Place reusable query logic in model scopes, not in controllers or services.

## Routes & Controllers
- Register routes in `routes/api.php`; use route model binding for all resource endpoints.
- Use resource controllers (`php artisan make:controller --resource`) for standard CRUD.
- Use single-action controllers with `__invoke` for non-CRUD endpoints.
- Keep controllers thin: validate with Form Requests, execute with Services/Actions, return JSON Resources.
- Return `JsonResource` objects — never return Eloquent models directly from API controllers.

## Eloquent ORM
- Define relationships explicitly with proper foreign key parameters: `hasMany(Order::class, 'customer_id', 'id')`.
- Use eager loading to prevent N+1: `Order::with(['customer', 'items.product'])->paginate(20)`.
- Use `whenLoaded('items')` in API Resources for conditional relationship inclusion.
- Define `$casts` for type coercion: `protected array $casts = ['status' => OrderStatus::class, 'metadata' => 'array']`.
- Use model events sparingly — prefer observers for complex lifecycle hooks.
- Scope queries: `scopeByStatus(Builder $query, OrderStatus $status): Builder`.

## Validation
- Use Form Request classes for all validation; never validate inline in controllers.
- Use the `Rule` class for complex rules: `Rule::unique('orders')->ignore($order->id)`.
- Create custom `Rule` classes for domain-specific validation: `php artisan make:rule ValidCouponCode`.
- Return clear validation messages: override `messages()` and `attributes()` in Form Requests.

## Authentication & Authorization
- Use Laravel Sanctum for API token authentication and SPA cookie-based auth.
- Define Policies for model-level authorization: `php artisan make:policy OrderPolicy --model=Order`.
- Call `$this->authorize('update', $order)` in controllers — never rely solely on frontend checks.
- Apply `can:update,order` middleware for route-level authorization guards.
- Use `Gate::allows('view-admin-panel')` for non-model permission checks.

## Queues & Jobs
- Use queues for all operations over ~200ms: email sending, PDF generation, external API calls.
- Keep jobs small and idempotent: pass record IDs and re-fetch in the job body.
- Set `$tries`, `$backoff`, and `$timeout` on every job class.
- Implement `failed(Throwable $exception)` to handle max-attempt exhaustion.
- Use `Queue::fake()` in tests and `Bus::assertDispatched(PlaceOrderJob::class)` for assertions.

## Testing
- Use `RefreshDatabase` trait for tests requiring a database; use `DatabaseTransactions` for faster, single-test transactions.
- Use factories with states: `Order::factory()->pending()->for($user)->create()`.
- Use `Http::fake()` to mock external HTTP calls; `Mail::fake()`, `Notification::fake()`, `Storage::fake()` for other side effects.
- Test authorization explicitly: assert 403 for unauthorized access, 200 for authorized.
- Run `php artisan test --parallel` in CI for faster test execution.

## Security
- Validate all input with Form Requests; use `$request->safe()->only(['field'])` when accessing validated data.
- Use `bcrypt` or `Hash::make` for passwords; never store plain text.
- Apply `throttle:api` middleware to authentication endpoints; use `RateLimiter::for` for custom limits.
- Use encrypted cookies and HTTPS; set `SESSION_SECURE_COOKIE=true` in production.
- Run `php artisan about` to audit configuration before deploying.

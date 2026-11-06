# React Performance Agent Rules

## Eliminating Render Waterfalls

- Move `await` to the branch that actually needs the result. Early-return paths must not block on unneeded fetches.
- Use `Promise.all()` for independent operations. Three sequential fetches become one round trip.
- Start all promises before awaiting any of them. Await only what each step strictly needs.
- In API routes and Server Actions, kick off all independent promises immediately and await them together at the end.
- Wrap only the sub-tree that needs data in `<Suspense>`. The rest of the page renders immediately without waiting.

## Bundle Size

- Import directly from source files, not barrel re-exports. Icon libraries with 1,500+ re-exports add hundreds of milliseconds of cold-start cost.
- Add heavy packages to `optimizePackageImports` in `next.config.js` to keep ergonomic imports while enabling direct-import transforms at build time.
- Use `next/dynamic` with `ssr: false` for editors, charts, maps, and anything not needed on initial render.
- Load large modules inside `useEffect` gated by a feature flag. Add `typeof window !== 'undefined'` to prevent SSR bundling.
- Load analytics, error tracking, and logging via `dynamic(..., { ssr: false })` to shift them post-hydration.
- Trigger `import('./heavy')` on `onMouseEnter` or `onFocus` to preload before the user clicks.

## Server-Side Performance

- Treat every `'use server'` function as a public API endpoint. Always verify auth and authorization inside the action itself — middleware alone is not sufficient.
- Split RSC data fetching into separate async components rendered side-by-side so Next.js fetches them in parallel.
- Wrap DB queries, auth checks, and expensive async work in `React.cache()` to deduplicate calls within a single request. Use primitive arguments, not inline objects, to get cache hits.
- Use module-level LRU caching for data that should survive across sequential requests within seconds.
- Pass only the fields the client actually uses across the RSC boundary. Every extra prop inflates the HTML payload.
- Wrap analytics, audit logs, cache invalidation, and notifications in `after(async () => {})` from `next/server`. The response sends immediately; the callback runs in the background.

## Client-Side Data Fetching

- Use SWR or TanStack Query so multiple component instances share one in-flight request.
- Deduplicate global event listeners with a module-level `Map<key, Set<callback>>` so N component instances share one actual DOM listener.
- Add `{ passive: true }` to `touchstart` and `wheel` listeners that do not call `preventDefault()`.
- Version localStorage keys (`key:v2`). Wrap all `getItem`/`setItem` calls in try-catch. Store only the minimum fields needed.

## Re-render Optimization

- If a value can be computed from props or state, compute it during render. Do not store it in state or sync it via `useEffect`.
- If state is only read inside a callback and not used in JSX, read it imperatively inside the handler instead of subscribing via hook.
- Do not use `useMemo` for simple boolean, string, or number expressions. Hook overhead exceeds computation cost.
- Extract default function, array, and object props to module-level constants so `memo()` comparisons are not broken by new references on every parent render.
- Depend on `user.id` not `user`. Depend on a derived boolean computed outside the effect, not a raw dimension.
- If a side effect is triggered by a user action, put it in the event handler. The effect + state pattern causes extra renders.
- Use `setItems(prev => [...prev, item])` to avoid stale closures and remove the state variable from `useCallback` deps.
- Use `useState(() => expensiveInit())` so the initializer runs only once.
- Wrap filter and search state updates in `startTransition` to keep input responsive during heavy re-renders.
- Use `useRef` for frame counts, timers, and animation state — values that change frequently but do not need to trigger re-renders.
- Subscribe to a derived boolean like `useMediaQuery('(max-width: 767px)')` rather than a raw `useWindowWidth()` that re-renders on every pixel.

## Rendering Performance

- Move JSX that never changes outside the component or to module scope.
- Use ternary or `{condition && <Component />}`. Never rely on `{count && <C />}` — renders `0` when count is zero.
- Use `isPending` from `useTransition` instead of manual `isLoading` state.
- For timestamps or client-only values, use `useSyncExternalStore` with a stable `getServerSnapshot`. Apply `suppressHydrationWarning` only on the specific element with an expected mismatch.
- Apply `content-visibility: auto` on tall off-screen list sections to skip layout and paint without JS virtualization.
- Round SVG coordinates to 1–2 decimal places. Animate wrapper `<div>` transforms rather than SVG attributes directly.

## JavaScript Performance

- Batch all DOM reads before all DOM writes. Never interleave `getBoundingClientRect()` with style mutations.
- Build a `Map<id, item>` once for repeated lookups instead of nested `array.find()`.
- Combine multiple `.filter()` or `.map()` chains into a single `for...of` loop when processing large arrays.
- Cache `arr.length` and deeply nested property accesses in local variables inside hot loops.
- Cache `localStorage.getItem` calls in a module-level `Map`. Invalidate on `storage` events and `visibilitychange`.
- Check `a.length !== b.length` before deep-comparing or sorting arrays.
- Return as soon as the result is determined. Do not process remaining items.
- Create RegExp patterns at module scope or inside `useMemo`. Never construct `new RegExp(...)` inside a render body without memoization. Be aware that the `g` flag has mutable `lastIndex` state.
- Use a single-pass loop to find min or max instead of `sort()`.
- Convert repeated `Array.includes()` checks in loops to `Set.has()`.
- Use `toSorted()`, `toReversed()`, `toSpliced()`, and `with()` to avoid mutating prop or state arrays.

## Advanced Patterns

- Use a module-level `let didInit = false` flag inside `useEffect` for one-time app initialization. React re-mounts components in StrictMode dev, so a bare empty-dep effect runs twice.
- Wrap event handler props passed to effects in `useEffectEvent` to get a stable reference that always calls the latest version without re-subscribing.
- Wrap debounced search callbacks in `useEffectEvent` so the debounce effect only re-runs when the query changes, not when the parent re-renders.


## Task Execution Patterns
- Before writing code, outline the approach in comments.
- After implementing a feature, write or update relevant tests.
- When fixing a bug, add a regression test.
- Check for linting issues before considering a task complete.

# Implement Web UI authentication flow and the typed API/WebSocket client layer

## Summary
Implement the login screen (token entry + validation), token storage, a fully typed API client for every DESIGN §7.2 endpoint, and a resilient WebSocket hook with reconnect — the data layer all UI pages (27–30) consume.

## Context
The hub uses one operator Bearer token (§7.1). The UI must make auth failures obvious, never leak the token, and give pages a uniform, typed way to fetch and subscribe.

## Scope
- `web/src/api/types.ts`: TS interfaces mirroring server schemas (Camera, Sensor, Reading, Event, Appliance, Action, Run, SystemInfo, WsMessage union per `docs/api/ws.md`).
- `web/src/api/client.ts`: `ApiClient` wrapping `fetch` — base `/api/v1`, Bearer header injection, problem+json error parsing into `ApiError {status, title, detail}`, JSON + blob (snapshot) helpers, all §7.2 endpoints as named methods.
- `web/src/api/ws.ts`: `useLiveUpdates(handler)` hook — mint ticket → connect → dispatch typed messages; reconnect with backoff 1→30 s; `gap` marker surfaces as a `resync` callback.
- `web/src/auth/`: `LoginPage` (token input, "where do I find my token" helper text pointing at the serve banner / `token regenerate`), `AuthProvider` (context: token, login(token) → validates via `GET /system/info`, logout), route guard redirecting unauthenticated to `/login`.

## Detailed Requirements
1. Token storage: `localStorage['iotify.token']` (documented trade-off, DESIGN §12.2 T6); never logged, never in URLs (except never — tickets go in URLs, tokens do not); logout clears storage and in-memory state.
2. 401 from authenticated API calls → global handler: clear token, redirect to `/login` with a "session invalid" note (single toast, no loops). Login validation handles its own 401 locally and surfaces the problem+json detail inline before any global redirect/clear path runs.
3. `ApiClient` request defaults: `Accept: application/json`, 15 s timeout via `AbortController`, no retries (UI shows errors; retry is a user action).
4. WS hook lifecycle: connect only when authenticated + page mounted; visibilitychange pauses reconnection when tab hidden > 5 min; clean close on logout; expose `status: 'connecting'|'live'|'reconnecting'|'off'` for a header indicator.
5. All §7.2 endpoints typed and covered by at least one vitest each using a fetch mock (msw or hand-rolled): success + problem+json error path.
6. Shared UI primitives introduced here (used by 27–30): `useApi()` hook, `<ErrorNote>`, `<ConfirmDialog>`, `<Spinner>`, toast mechanism — minimal, CSS-module styled, no component library (ADR-003).
7. Login page must not echo the token (input `type=password`, no value in DOM after submit beyond storage).

## Acceptance Criteria
- [ ] Login with bad token shows the problem+json detail; good token lands on `/dashboard`; refresh keeps session; logout returns to login with storage cleared.
- [ ] Simulated 401 mid-session (mock) triggers exactly one redirect+toast.
- [ ] Login validation 401 does not trigger the global session-invalid toast/redirect loop; only non-login authenticated calls do.
- [ ] WS hook: ticket mint + connect + typed dispatch verified against a mock WS server (vitest + `ws` polyfill or msw-ws); reconnect backoff sequence asserted with fake timers; `gap` triggers `resync`.
- [ ] `tsc --noEmit` strict passes; every client method has a type test (request/response shapes compile against fixtures copied from server OpenAPI examples).
- [ ] No token string appears in console logs or URLs (grep test over emitted logs in vitest).

## Validation
`npm test` (vitest suites for client/auth/ws) in CI web job; manual smoke against a real hub documented in PR (login → header shows `live`).

## Dependencies
25, 16, 19 (`docs/api/ws.md`).

## Non-goals
No page implementations (27–30), no multi-user, no remember-me/expiry logic (token is long-lived until rotated).

## Design References
DESIGN §7.1–7.4, §11.1, §12.2 T6; docs/api/ws.md (issue 19).

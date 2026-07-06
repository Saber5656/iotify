# Implement the FastAPI application skeleton, lifecycle wiring, and token authentication

## Summary
Implement `iotify.server.app` (app factory + startup/shutdown of DB, scheduler, pipeline, retention job), `iotify.server.auth` (Bearer token auth per DESIGN §7.1), security headers, and the `iotify serve` CLI command.

## Context
This is the hub's assembly point: everything built in waves 0–2 starts here, and every later surface (REST/WS/UI/CLI/menu bar) authenticates through this layer. Auth rules come from ADR-004-2/3.

## Scope
- `src/iotify/server/app.py`: `create_app(config, secrets, deps) -> FastAPI` with lifespan managing: Database open/migrate → EventBus → CaptureScheduler → SensorPipeline → retention task (every 6 h) → graceful shutdown in reverse order. `deps` dataclass enables test injection.
- `src/iotify/server/auth.py`: `require_token` dependency; first-run token generation; failed-auth rate limiter.
- CLI: `iotify serve [--host] [--port] [--config-dir] [--data-dir] [--json-logs]` (flags override config); `iotify token regenerate`.
- Middleware: security headers, request logging (path, status, ms — no bodies), problem+json error handler.

## Detailed Requirements
1. **Token lifecycle**: if `secrets.api_token_sha256` missing at startup → generate 32 random bytes (`secrets.token_urlsafe(32)`), print the plaintext token to stdout inside an unmissable banner (once), store sha256 hex via `write_secrets`. `iotify token regenerate` does the same rotation and exits (refuses while a hub process holds the DB? — no lock check in v1; document that restart is required).
2. `require_token`: parse `Authorization: Bearer <t>`; compare `sha256(t)` to stored hash via `hmac.compare_digest`; 401 problem+json on missing/bad. Applied via router-level dependency to **all** `/api/v1` routes; exemptions: `GET /healthz` (returns literal `ok`, no JSON, no version), static assets mount `/` (issue 25).
3. Rate limit: sliding 60 s window per client IP, max 10 auth failures → 429 with `Retry-After: 60`; counter in-memory; successes unaffected. X-Forwarded-For honored only when `server.trust_proxy: true` (new config key, default false — add to §5.2 model in this issue).
4. Security headers on every response: `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` on `/api/**`; CSP for HTML/static: `default-src 'self'; img-src 'self' data:; connect-src 'self' ws: wss:; frame-ancestors 'none'` (final CSP tuned in issue 25).
5. Bind behavior: default from config (`127.0.0.1`); when host is non-loopback log the ADR-004-3 warning banner (mentions token, TLS guide, do-not-port-forward).
6. Error handling: all handlers return RFC 9457 problem+json (`type`, `title`, `status`, `detail`); unexpected exceptions → 500 with generic detail (no stack traces to clients), full trace logged.
7. `GET /api/v1/system/info`: version, uptime_s, camera health map, sensor count, per-sensor last_read age, MQTT/HA connection placeholders (`"disabled"` until issues 20/22), DB size bytes, queue depths (from pipeline metrics).
8. CORS: not enabled (same-origin UI); explicitly no `CORSMiddleware`.
9. `create_app` must run with scheduler/pipeline against an empty DB (zero cameras) — clean idle startup, `system.started` event emitted.

## Acceptance Criteria
- [ ] First run prints a token banner exactly once and writes hashed secrets file (mode 0600).
- [ ] Requests without/with-wrong token → 401 problem+json; with token → 200; `/healthz` works unauthenticated; 11th failure within 60 s → 429.
- [ ] `hmac.compare_digest` used (code review + test tolerance).
- [ ] Security headers present on API and root responses; no `Server` header leaking uvicorn version (`server_header=False`).
- [ ] `iotify serve` boots with empty config dir, `system/info` returns sane values, Ctrl-C shuts down cleanly ≤ 5 s (scheduler joined, DB closed).
- [ ] Non-loopback bind logs the warning banner (test with `--host 0.0.0.0` capture).
- [ ] `token regenerate` rotates: old token 401s after restart, new one works.

## Validation
`pytest tests/unit/server/test_auth.py tests/integration/test_app_lifecycle.py` (httpx `ASGITransport` client; real tmp DB + replay camera boot).

## Dependencies
02, 03, 04, 09, 15.

## Non-goals
No resource routers (17/18), no WS (19), no static UI mount (25), no TLS.

## Design References
DESIGN §7.1–7.3, §13; ADR-004-2/3/4.

# Scaffold the Web UI (React + TypeScript + Vite) and integrate its build with the hub

## Summary
Create the `web/` SPA scaffold (React 18 + TS + Vite), wire `web/dist` static serving into FastAPI with SPA fallback and final CSP, add dev-proxy ergonomics, and extend CI to lint/typecheck/test/build the web app.

## Context
ADR-003 fixes the web stack; DESIGN §11.1 lists the pages. This issue delivers the empty-but-running shell that issues 26–30 fill in, plus the packaging path that lets the wheel/Docker embed built assets (issues 38/39).

## Scope
- `web/`: Vite scaffold (`react-ts` template), `package.json` (+ committed `package-lock.json`), eslint (typescript + react-hooks presets), prettier config, vitest setup, `src/` skeleton: `main.tsx`, `App.tsx`, router (react-router) with routes `/login /dashboard /cameras /sensors/:id /appliances /events /settings` rendering placeholder components, shared layout (sidebar nav + header), CSS modules convention, dark-mode-respecting base styles.
- Hub side: `src/iotify/server/static.py` — mount built assets from `importlib.resources` path `iotify/server/static/` when present, else 404 JSON hinting `make web-build`; SPA fallback (all non-`/api`, non-asset GETs → `index.html`); asset cache headers (`immutable` for hashed files, `no-cache` for `index.html`).
- Build plumbing: `make web-dev` (vite dev server, proxy `/api` + `/api/v1/ws` websocket to `127.0.0.1:8799`), `make web-build` (vite build → copy into `src/iotify/server/static/`, dir gitignored).
- CI: add `web` job (node 22, `npm ci`, eslint, `tsc --noEmit`, vitest, build; upload dist artifact).

## Detailed Requirements
1. Final CSP header for HTML responses (supersedes issue 16 placeholder): `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'none'` — no third-party origins ever (ADR-004-1); fonts system-stack only.
2. No runtime dependency added beyond: react, react-dom, react-router, recharts (declared now, used in 29); dev-only tooling as above. Every later dep addition needs a rationale line (DESIGN §12.3-5).
3. Vite `base: '/'`; hashed filenames on build; bundle budget: initial JS ≤ 300 KB gzipped (CI check via a small script reading `dist/` sizes; warning at 250 KB, fail > 300 KB).
4. Placeholder pages render a titled empty state; login route renders an unstyled token form placeholder (real auth in 26).
5. `web/README.md`: dev workflow (two terminals: `iotify serve` + `make web-dev`), build workflow, proxy notes.
6. Node version pinned via `web/.nvmrc` (22) and `engines` field; CI honors it.

## Acceptance Criteria
- [ ] `make web-build && iotify serve` serves the SPA shell at `/` with SPA fallback (`/dashboard` deep link works, `/api/v1/system/info` still 401s without token).
- [ ] Dev proxy: UI on the Vite port reaches the hub API and WS without CORS errors (documented smoke, screencast optional).
- [ ] CI `web` job green: eslint, tsc, vitest (one placeholder test), build + size budget.
- [ ] CSP header present on `index.html` responses exactly as specified; hashed assets get `immutable` caching.
- [ ] Fresh clone without `make web-build` → hub still boots; `/` returns the actionable 404 hint.

## Validation
CI web job + `pytest tests/integration/test_static_serving.py` (with a fixture-built minimal dist).

## Dependencies
16 (app), 05 (CI base).

## Non-goals
No real pages/data fetching (26–30), no i18n strings beyond scaffold constant file, no SSR, no PWA.

## Design References
DESIGN §11.1, §7.1 (CSP/auth posture), ADR-003, ADR-004-1/6.

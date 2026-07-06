# ADR-003: Technology stack

Status: Accepted (2026-07-06)
Deciders: design agent (conservative defaults; owner may override before implementation starts)

## Context

Implementation will be executed by lower-capability agents working from granular issues. The stack must be mainstream (well-represented in their training data), mechanical to test, and cross-platform (macOS/Linux, amd64/arm64).

## Decision

| Layer | Choice | Rationale |
|---|---|---|
| Hub language | Python ≥ 3.11 (floor = Debian Bookworm / Pi OS system Python) | CV ecosystem, contributor accessibility |
| Web framework | FastAPI + uvicorn | Typed, OpenAPI for free, WS support |
| Validation/config | pydantic v2 + pydantic-settings | Schema-first configs, `extra="forbid"` |
| Vision | `opencv-python-headless` + numpy (classical CV only in v1) | No GPU/model runtime needed for led/sevenseg/change |
| MQTT | aiomqtt (asyncio) | Async-native; K4 fallback: paho-mqtt |
| DB | SQLite via aiosqlite, WAL; hand-written sequential SQL migrations | Zero-ops, single-file backup; ORM adds more risk than value at this size |
| HTTP client | httpx | Timeouts/limits API, async |
| CLI | Typer + rich tables | Mechanical to extend |
| Packaging | hatchling, src layout, `uv` for dev env + `uv.lock` | Reproducible, fast CI |
| Lint/type | ruff + mypy | Standard gates |
| Web UI | React 18 + TypeScript + Vite (SPA served as static files by the hub); Recharts for history charts; no CSS framework lock-in (CSS modules) | Highest familiarity for implementation agents; single-binary-ish deploy preserved by embedding `web/dist` in the wheel |
| Menu bar app | Swift 5.9+, SwiftUI `MenuBarExtra`, SwiftPM, macOS 13+; Keychain for token; `SMAppService` for login item | Native menu bar UX the owner selected for v1; SwiftPM keeps it Xcode-project-free |
| License | Apache-2.0 (default; **human confirmation required before first public release** — DESIGN §16 K9) | Patent grant suits a device-adjacent ecosystem |

## Options considered (deltas only)

- **Rust hub**: better perf, worse contributor/implementation-agent throughput for CV glue; rejected.
- **Svelte/htmx UI**: fewer node deps but less agent familiarity; rejected.
- **SQLAlchemy**: abstraction cost > value for ~8 tables; rejected.
- **rumps / xbar for menu bar**: cheaper but delivers a degraded experience against an explicit owner selection; rejected.

## Consequences

- Two toolchains (Python + Node) plus Swift for the menu bar; CI must build all three (ISSUE_PLAN wave 0/7).
- The wheel embeds built web assets — release workflow must build web before packaging (issue 39).
- Classical-CV-only is a bet tracked by K1 (tiny-CNN fallback issue if accuracy targets miss).

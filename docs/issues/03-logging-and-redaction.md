# Implement structured logging with secrets redaction

## Summary
Implement `iotify.logging_setup`: application-wide logging configuration (console text + optional JSON), per-module loggers, and a root-installed redaction filter that prevents secrets from ever appearing in logs.

## Context
DESIGN §13 requires structured logs; ADR-004-4 requires that secrets are never logged. The redaction filter is a security control, not cosmetics — later issues (MQTT, HA client, auth) rely on it.

## Scope
- `src/iotify/logging_setup.py`: `setup_logging(level: str, json_output: bool = False) -> None`; `RedactionFilter(logging.Filter)`; helper `get_logger(name)` (thin `logging.getLogger` wrapper for consistent naming `iotify.<module>`).

## Detailed Requirements
1. Text format: `2026-07-06T12:00:00.123Z LEVEL iotify.module message key=value`; JSON format: one object per line with `ts`, `level`, `logger`, `msg`, plus `extra` fields.
2. Level from config (`logging.level`), overridable by `IOTIFY_LOGGING__LEVEL`.
3. `RedactionFilter` masks, in both `msg` and formatted args/extras:
   - values of keys matching (case-insensitive) `password|token|secret|authorization|api_key`,
   - `Bearer <anything>` patterns,
   - `rtsp://user:pass@host` and `http(s)://user:pass@host` URL userinfo (replace pass with `***`),
   replacement string exactly `***`.
4. Filter is installed on the root handler so third-party library records pass through it too.
5. uvicorn/aiomqtt loggers are re-leveled to WARNING unless `logging.level == "debug"`.
6. `setup_logging` is idempotent (safe to call twice; no duplicate handlers).
7. Timestamps are UTC with `Z` suffix.

## Acceptance Criteria
- [ ] `logger.info("connecting", extra={"password": "hunter2"})` emits `password=***`.
- [ ] Logging the string `rtsp://admin:hunter2@10.0.0.5/stream` emits `rtsp://admin:***@10.0.0.5/stream`.
- [ ] `Authorization: Bearer abc.def` never appears verbatim in any handler output.
- [ ] JSON mode produces parseable one-line JSON records with `ts/level/logger/msg`.
- [ ] Calling `setup_logging` twice does not duplicate output lines.
- [ ] mypy strict + unit tests pass.

## Validation
`pytest tests/unit/logging` with a capture handler asserting each redaction case; grep-based test that no test fixture secret string escapes redaction.

## Dependencies
01-repo-scaffold-python-package, 02-config-schema-and-loader (level wiring).

## Non-goals
No log shipping, no rotation (systemd/Docker own that), no metrics endpoint (v2 K-list).

## Design References
DESIGN §13, ADR-004-4, DESIGN §12.3-2.

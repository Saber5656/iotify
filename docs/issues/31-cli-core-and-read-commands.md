# Implement CLI client core and read commands (status, cameras, sensors, events, export/import)

## Summary
Implement the `iotify` client-side CLI per DESIGN §11.2: hub connection config, `status`, `camera list/snapshot`, `sensor list/read/watch`, `events tail`, and `entities export/import` — human tables by default, `--json` for scripts.

## Context
The CLI is the Mac engineer's surface (P-2) and the scripting substrate for Raycast/Alfred/cron. It reuses the same REST/WS contracts as the Web UI. `serve`/`token` commands already exist (16); this issue adds the client side.

## Scope
- `src/iotify/cli/client.py` (httpx sync client wrapper + config resolution), `render.py` (rich tables/json), command modules `cmd_status.py`, `cmd_camera.py`, `cmd_sensor.py`, `cmd_events.py`, `cmd_entities.py`; wiring into `cli/main.py`.

## Detailed Requirements
1. Connection resolution precedence: flags `--hub/--token` → env `IOTIFY_HUB_URL`/`IOTIFY_TOKEN` → config file `~/.config/iotify/cli.toml` (`[hub] url = …, token = …`, file mode-checked like secrets: warn if group/other-readable). `iotify login` command: prompts for URL+token (hidden input), validates via `/system/info`, writes cli.toml `0600`.
2. Commands:
   - `iotify status` — hub version/uptime, camera health table, MQTT/HA connection states, sensor count (from `/system/info`);
   - `iotify camera list`; `iotify camera snapshot <id> -o out.jpg [--fresh]` (writes bytes; refuses to overwrite without `--force`);
   - `iotify sensor list` (id, name, type, camera, last value, age, availability);
   - `iotify sensor read <id> [--debug]` — test-read, prints value/confidence (+debug image paths written to a temp dir with `--debug`);
   - `iotify sensor watch [<id>…]` — WS live stream (ticket flow) printing one line per update (`ts  sensor  value  conf`); `--json` = NDJSON; Ctrl-C exits 0; auto-reconnect with notice; on WS `gap` marker or reconnect, refetch latest state for watched sensors and emit any changed current values before resuming live output;
   - `iotify events tail [--kind …] [-n 50] [--follow]` — history then follow via WS;
   - `iotify entities export -o entities.json` / `entities import entities.json [--dry-run]` — cameras+sensors+appliances round-trip (passwords excluded from export with a stderr note; import creates-or-updates by id, reports per-entity result, `--dry-run` validates only);
   - `iotify diag -o diag.tar.gz [--include-snapshots]` — debug bundle per DESIGN §13: versions, `/system/info` snapshot, redacted config (secrets stripped by key, reusing the issue-03 redaction patterns), recent events; **no images** unless `--include-snapshots`; bundle must pass the canary-secret leak check (issue 36 suite covers it).
3. Output discipline: human tables via rich to stdout; logs/notices to stderr; `--json` on every read command emits machine-stable shapes (documented in `docs/api/cli.md`, created here); exit codes 0 ok / 1 transport-or-API error / 3 not-found (2 is reserved for verification failure, issue 32).
4. Errors: problem+json rendered as `error: <title> — <detail>` on stderr; connection refused → hint to check `--hub`/serve status.
5. WS in sync CLI: implement with `websockets` sync client or httpx-ws (add dep with rationale); reuse ticket endpoint.
6. No pagination flags in v1 (server has none) — `-n/--limit` maps to server `limit` where supported.

## Acceptance Criteria
- [ ] All commands green against a booted test hub (integration tests spawn `create_app` + run CLI via `typer.testing.CliRunner` with real HTTP through ASGI transport or a live uvicorn on an ephemeral port — pick one, document).
- [ ] `--json` outputs parse and match documented shapes (golden files under `tests/fixtures/cli/`).
- [ ] `login` writes `0600` cli.toml; world-readable existing file triggers the warning.
- [ ] `sensor watch` receives a replay-driven state change ≤ 1 s (integration, marked slow) and recovers missed state after a simulated WS gap/reconnect by refetching latest state.
- [ ] `entities export` → wipe DB → `import` reproduces the entity set (passwords empty, warning shown); `--dry-run` mutates nothing.
- [ ] Exit codes verified per matrix above; stdout/stderr separation asserted (pipe tests).

## Validation
`pytest tests/integration/test_cli.py` + golden JSON tests; manual smoke on macOS terminal in PR.

## Dependencies
16, 17, 18, 19.

## Non-goals
No appliance commands (32), no shell completion polish (Typer default only), no TUI.

## Design References
DESIGN §11.2, §7.1–7.4; ADR-004-4 (client-side token file hygiene).

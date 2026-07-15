# Implement CLI appliance control commands with verification progress

## Summary
Implement `iotify appliance list` and `iotify appliance run <appliance> <action>` with param passing, verification progress rendering, `--wait/--no-wait`, and scripting-grade exit codes — the US-5 terminal experience.

## Context
Terminal control is the fastest Mac surface and the automation hook (Raycast/scripts). It must map the §9.4 run lifecycle to honest exit codes so scripts can rely on it.

## Scope
- `src/iotify/cli/cmd_appliance.py` wired into `cli/main.py`.

## Detailed Requirements
1. `iotify appliance list`: table — id, name, actions (name + param names + verify badge), warnings (`verify_sensor_missing` flagged); `--json` mirrors API.
2. `iotify appliance run <appliance_id> <action> [--param k=v]* [--no-verify] [--no-wait] [--timeout-extra 30]`:
   - params: repeated `--param temperature=26`; values passed as strings (server coerces using action param metadata per §9.2); missing/extra/invalid typed params surface the server 400 verbatim;
   - dispatch → `202 {run_id}`; `--no-wait` prints `run_id` and exits 0 immediately;
   - default wait mode: subscribe WS (`verification_update` filtered by run_id; fallback: poll `runs/{id}` every 1 s when WS unavailable) rendering a single self-updating status line (rich): `SENDING (attempt 1/3) → VERIFYING 12s/20s → VERIFIED in 8.2s`; non-TTY stdout → plain line per transition;
   - client-side safety timeout: server-derived worst case `(settle+timeout_s)×(1+retries) + timeout-extra` then exit 1 with "gave up waiting (run may still complete)" + run_id.
3. Exit codes: `0` VERIFIED or DONE_UNVERIFIED; `2` FAILED_TIMEOUT / FAILED_SERVICE / ABORTED (verification-level failure — scripts branch on this); `1` transport/API errors incl. 409-busy (busy also prints the running run_id); `3` unknown appliance/action.
4. `--json` in run mode: NDJSON transition stream, terminal object last (documented in `docs/api/cli.md`).
5. `iotify appliance runs <appliance_id> [-n 10]`: recent terminal runs from events (mirrors UI drawer, issue 30-5).

## Acceptance Criteria
- [ ] Against stub HA + replay led camera (issue 24 harness): run → VERIFIED path exits 0 with rendered progress; forced-timeout path exits 2 after showing attempts.
- [ ] 409-busy prints running run_id, exits 1; unknown action exits 3.
- [ ] `--no-wait` returns immediately with run_id; later `runs` shows the terminal state.
- [ ] WS-unavailable fallback (WS route disabled in test app) completes via polling with identical exit semantics.
- [ ] Non-TTY output is line-oriented (no ANSI control sequences) — asserted by piping.
- [ ] NDJSON stream golden-tested.

## Validation
`pytest tests/integration/test_cli_appliance.py` reusing the issue-24 verification harness.

## Dependencies
31, 23, 24.

## Non-goals
No local scheduling/retry loops beyond server semantics, no interactive picker UI, no macro composition.

## Design References
DESIGN §11.2, §9.2–9.4; issue 24 endpoint semantics.

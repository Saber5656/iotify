# Build the end-to-end scenario test suite (compose stack: hub + Mosquitto + stub HA + replay cameras)

## Summary
Assemble the full-product E2E suite: a docker-compose test profile (or in-process equivalent) wiring hub + Mosquitto + stub Home Assistant + scripted replay cameras, executing the flagship scenarios (discovery → sensing → verified control → failure/retry) as CI-runnable assertions — the v1 completion proof.

## Context
Unit/integration layers verify parts; this suite verifies the *product claims* (DESIGN §14 E2E row): a sensor appears in HA-land, states flow, and verified control retries honestly. It reuses `tests/helpers/stub_ha.py` (24) and the replay source (06), and doubles as the release-gate automation behind 40's checklist.

## Scope
- `tests/e2e/`: `compose.e2e.yaml` (hub image from issue 38 build or local build target, mosquitto with auth, stub-HA container wrapper), scenario driver (`pytest -m e2e`), scripted replay assets (lamp-off→on sequence; sevenseg count sequence; change sequence), MQTT capture helper, and a `make e2e` target; CI job on Linux (nightly + on-demand label, not per-PR — runtime budget).

## Detailed Requirements
1. **Scenario A — onboarding & discovery**: boot stack with empty config → create camera (replay lamp) + led sensor via API → assert retained HA discovery config + availability + initial state on the broker within 10 s; restart-simulation: new subscriber (clean session) receives everything retained.
2. **Scenario B — sensing truth**: drive the lamp sequence → assert exactly one `state=on` transition (stabilizer honest under the flickery frames included in the fixture), reading persisted, WS client observed `sensor_update`, dashboard latest API agrees.
3. **Scenario C — verified control happy path**: appliance `power_on` with verify on the lamp sensor; stub HA programmed: service call flips the replay source to the "on" sequence (stub exposes a control hook the driver calls) → run reaches VERIFIED; MQTT result payload asserted; end-to-end latency logged.
4. **Scenario D — retry then fail**: stub HA accepts calls but lamp never turns on → exactly `1+retries` service calls observed at stub, terminal FAILED_TIMEOUT, WS transition order asserted, exit-code path also asserted via `iotify appliance run` CLI (reusing 32).
5. **Scenario E — degradation honesty**: kill the camera container/source mid-run → sensor availability offline propagates to MQTT availability topic and `readings/latest`; verify-attempt during outage fails fast with `sensor_unavailable`.
6. Determinism: replay sequences + fake-free real timing with generous-but-bounded asserts (≤ 10 s windows); zero sleeps > 1 s in polling loops; total suite ≤ 10 min.
7. Artifacts on failure: hub logs, broker capture (all topics), stub-HA call log, and final DB copied to CI artifacts.
8. The suite must run BOTH via compose (CI/nightly, exercising the real image) and in-process (dev fast path `make e2e-local`, reusing integration fixtures) — scenario code shared, transport parametrized.
9. Document in `docs/qa/e2e.md`: how to run, extend, and read failures; mapping table scenario ↔ user story (US-1…US-5) ↔ DESIGN sections.

## Acceptance Criteria
- [ ] All five scenarios green in compose mode on CI (nightly workflow evidence) and in-process mode locally.
- [ ] Scenario ↔ user-story mapping covers US-1 through US-5 with no gaps.
- [ ] Deliberate regression (raise stabilizer agree to impossible value in a scratch branch) fails Scenario B — proving sensitivity — then reverted (evidence).
- [ ] Failure artifacts appear on a forced failure run.
- [ ] Suite runtime ≤ 10 min; flake rate: 3 consecutive clean nightly runs before closing.

## Validation
Nightly CI runs + the deliberate-regression sensitivity check + 3-run stability streak.

## Dependencies
38 (image), 32 (CLI path), 24 (stub HA + verification), 21 (discovery), 15, 09, 06.

## Non-goals
No real-HA container automation (manual checklist covers it, issue 40), no performance/load testing (budgets tracked in unit perf logs), no browser E2E beyond the Playwright smoke (25/29 scope).

## Design References
DESIGN §14 (E2E row), §1.1 (user stories), §15; issues 24/38 harness reuse.

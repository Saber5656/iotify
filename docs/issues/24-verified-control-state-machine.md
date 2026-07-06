# Implement the verified-control state machine and run endpoints

## Summary
Implement `iotify.control.verify` — the DESIGN §9.4 run state machine (dispatch → settle → verify via stable sensor readings → retry → terminal) — plus `POST /appliances/{id}/actions/{name}/run` and `GET /appliances/runs/{run_id}`, with progress on the bus, WS, and MQTT result topic.

## Context
This is the product's headline feature (research takeaway 5): IR/BLE actuation is open-loop; iotify closes the loop with the camera. Correct concurrency, timeout, and failure semantics are the whole point.

## Scope
- `src/iotify/control/verify.py`: `VerificationEngine` — `run(appliance_id, action_name, params, verify: bool) -> RunHandle`, in-memory run registry (ring of last 100), per-appliance mutex.
- Run endpoints in `src/iotify/server/api/appliances.py`.

## Detailed Requirements
1. **Dispatch**: render `service_data` templates with `params` (strict §9.2: missing param → 400 before any state change; extra params → 400); transition PENDING→SENDING; call `HaClient.call_service`.
2. **No verify clause or `verify=false`**: HA 2xx → terminal `DONE_UNVERIFIED`; HA error → `FAILED_SERVICE {error, ha_message}`.
3. **Verify path**: after 2xx wait `settle_delay_s` (AWAITING_EFFECT) then VERIFYING: subscribe to the verify sensor's **stable** outputs (bus `sensor.state_changed` + current last stable value from pipeline — evaluate immediately in case the state was already reached);
   - expectation evaluation per §9.3 (implement all five keys; `changed_within_s` = a change event with ts ≥ dispatch_ts within n seconds);
   - met → `VERIFIED` (record `verify_latency_ms`);
   - `verify_timeout_s` elapsed → attempt += 1; if attempt ≤ 1+`verify_retries` → re-dispatch (back to SENDING; re-render templates once, reuse); else `FAILED_TIMEOUT`;
   - verify sensor unavailable at start or becomes unavailable → fail fast `FAILED_TIMEOUT` variant `{reason:"sensor_unavailable"}` **without** retries (a blind retry with no working sensor is spray-and-pray; documented §9.4).
4. Concurrency: per-appliance asyncio lock; busy → API 409 `{running_run_id}`; global cap 4 concurrent runs (503 beyond, `Retry-After: 5`); shutdown → in-flight runs → `ABORTED` (lifespan hook order: engine stops before HA client closes).
5. Every transition: bus `verification.update {appliance_id, action, run_id, state, attempt, detail?}` → events table + WS (`verification_update`); terminal states additionally MQTT `iotify/appliance/<id>/result` (QoS 1, not retained) `{run_id, action, state, attempts, started_ts, ended_ts, verify_latency_ms?}`.
6. `RunHandle`/`GET runs/{run_id}` shape: `{run_id, appliance_id, action, state, attempt, params, verify: bool, transitions: [{state, ts}], result?}`; unknown run → 404 (registry is in-memory; document restart loss, DESIGN §9.4).
7. Timing uses the injected clock abstraction (fake-clock tests); no `sleep` loops — event-driven waits with `asyncio.wait_for`.
8. `verify_sensor_missing` warned actions (issue 23-4) run unverified with the warning copied into the run record.

## Acceptance Criteria
- [ ] Happy path (stub HA 2xx + replay-camera led flips on): PENDING→…→VERIFIED, one MQTT result, WS updates in order, latency recorded.
- [ ] Retry path: sensor never flips → exactly `1+retries` service calls at correct fake-clock times → FAILED_TIMEOUT.
- [ ] Already-satisfied expectation verifies without waiting for a new reading.
- [ ] HA 500 → FAILED_SERVICE with HA message; no retry when retries=0 semantics honored (`retries` counts *verification* retries, not HTTP).
- [ ] Busy appliance → 409 with running id; 5th concurrent run → 503; shutdown mid-run → ABORTED terminal event emitted.
- [ ] Sensor unavailable mid-verify → fail fast, no further dispatches.
- [ ] `changed_within_s` verified against a change-reader replay sequence.
- [ ] Full state history retrievable via `runs/{id}` until ring eviction.

## Validation
`pytest tests/integration/test_verified_control.py` — booted app + stub HA (in-process FastAPI stub with programmable responses; created here under `tests/helpers/stub_ha.py`, reused by E2E issue 41) + replay cameras + Mosquitto for result topic.

## Dependencies
15, 20, 22, 23, 19 (WS visibility).

## Non-goals
No persistent run history table (events suffice, v2 if needed), no scheduling/queueing beyond mutex+cap, no multi-step scenes/macros (v2).

## Design References
DESIGN §9.2–9.4, §6.5, §8.1; ADR-002; research takeaway 5.

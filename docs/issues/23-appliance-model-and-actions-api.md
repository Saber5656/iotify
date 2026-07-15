# Implement the appliance/action model, CRUD API, and HA catalog proxy endpoints

## Summary
Implement `/api/v1/appliances*` (CRUD with embedded actions, per DESIGN §9.1), strict param-template validation (§9.2), expectation-DSL validation (§9.3), and the `/api/v1/ha/*` proxy endpoints that power UI pickers.

## Context
Appliances bind three worlds: HA entities (22), iotify sensors (verification), and named actions invoked by every control surface (24, 30, 32, 35).

## Scope
- `src/iotify/server/api/appliances.py`, `ha.py`; `src/iotify/control/appliances.py` (validation + repo orchestration); schemas.

## Detailed Requirements
1. `POST/PUT /appliances` body per DESIGN §9.1 (appliance `{id, name, actions:[…]}`); actions replaced wholesale on PUT (replace-on-update, issue 04-3). Action fields: `{name, ha_domain, ha_service, target_entity, service_data?, param_types?, verify?}`; `param_types` is optional metadata `{param_name: "string"|"number"}` defaulting undeclared params to `"string"`; `verify` = `{sensor_id, expect, timeout_s?, retries?, settle_delay_s?}` with defaults 20/1/2 per §6.1.
2. Validation on write:
   - action name slug per §7.3; unique within appliance;
   - `ha_domain`/`ha_service`/`target_entity` shape-validated (§22-6 regexes); when HA is reachable also existence-checked (unknown entity/service → 422 with `warnings` escape hatch `?force=true` for offline authoring — force records `warnings:["unverified_ha_refs"]` in response);
   - `service_data`: JSON object; values may be scalars or `{{params.<key>}}` placeholder strings (regex `^\{\{params\.[a-z][a-z0-9_]*\}\}$` — whole-value only, no partial interpolation in v1); collect declared param names into response field `params: [{name, type}]`, where `type` comes from `param_types` or defaults to `"string"`; reject `param_types` keys that are not declared placeholders;
   - `verify.sensor_id` must reference an existing sensor; expectation key must be one of §9.3 and type-compatible with the sensor's reader (e.g., `number_gte` requires sevenseg) → 422 otherwise;
   - `changed_within_s` only valid for change-reader sensors.
3. `GET /appliances` / `GET /appliances/{id}`: include actions, declared params, verification summary, and `last_run` (from events, latest `verification.update` terminal state).
4. Deleting a sensor referenced by `verify_sensor_id`: DB sets NULL (issue 04); GET responses flag such actions `warnings:["verify_sensor_missing"]`; run attempts on them proceed **unverified** with the same warning in the run record (documented in §9.4 failure modes).
5. `GET /ha/entities?domain=&refresh=` and `GET /ha/services`: thin proxies over issue-22 client (cache semantics pass through); 503 problem+json `ha_unreachable` when HA down; 409 `ha_disabled` when disabled.
6. Bus event `appliance.updated` on CRUD (consumed by UI/WS clients as `event`).
7. Run endpoints (`…/run`, `runs/{id}`) are **not** in this issue (24 owns execution) — but route stubs must not exist (no dead endpoints).

## Acceptance Criteria
- [ ] CRUD happy path + every 422 rule above covered (incl. `?force=true` bypass recording warnings).
- [ ] DESIGN §9.1 example body round-trips verbatim (golden test).
- [ ] Param extraction: `{"temperature": "{{params.temperature}}"}`, `param_types: {"temperature":"number"}` → `params:[{"name":"temperature","type":"number"}]`; partial-interpolation `"temp={{params.t}}"` and undeclared `param_types` keys are rejected 422.
- [ ] Expectation/reader compatibility matrix tested (all §9.3 keys × 3 reader types).
- [ ] Sensor deletion flips referencing actions to warned state (GET reflects it).
- [ ] HA proxy endpoints: reachable/unreachable/disabled paths return 200/503/409 respectively (MockTransport).

## Validation
`pytest tests/integration/test_api_appliances.py tests/unit/control/test_appliance_validation.py`.

## Dependencies
16, 17 (sensors exist), 22, 04.

## Non-goals
No execution/state machine (24), no UI (30), no appliance MQTT exposure (ADR-002).

## Design References
DESIGN §9.1–9.3, §6.1 (appliance tables), §7.2–7.3.

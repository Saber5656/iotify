# Implement the Web UI appliance configuration and verified-control panel

## Summary
Implement the Appliances page: appliance/action CRUD with HA entity/service pickers, param forms, and the run experience — buttons that dispatch actions and render live verification progress (pending → sending → verifying → verified/failed with attempts) (US-3).

## Context
This is the visible face of the headline feature (verified control, DESIGN §9). It sits on issues 23 (CRUD + HA catalogs) and 24 (run endpoints + WS `verification_update`).

## Scope
- `web/src/pages/appliances/`: `AppliancesPage` (list), `ApplianceForm` (+`ActionEditor` rows), `RunButton`, `RunProgress`, `RunHistoryDrawer`.

## Detailed Requirements
1. **ApplianceForm**: id/name; actions as an editable list. Each `ActionEditor`: name slug; HA target pickers — domain select → `GET /ha/services` populated service select → entity autocomplete from `GET /ha/entities?domain=` (free-text fallback + `?force=true` flow when HA offline, surfacing `unverified_ha_refs` warning per issue 23-2); `service_data` editor = key/value rows where value is literal or "parameter" toggle (generates `{{params.<name>}}`, whole-value rule enforced); verify section (optional): sensor picker (filtered by expectation compatibility per §9.3 — picking the expectation first filters sensors, and vice versa), expectation editor per key type, timeout/retries/settle inputs with §6.1 defaults.
2. HA-down states: pickers degrade to free text with a banner ("HA unreachable — references can't be validated"); 409 `ha_disabled` renders setup pointer to config docs.
3. **Appliance cards** (list page): name + action buttons. Parameterless action → immediate run on click; with params → popover form (typed inputs: number/string inferred from param usage context — all strings in v1, numeric keyboard hint via `inputmode`), `verify` toggle default on when action has verify config.
4. **RunProgress**: on 202, subscribe (WS `verification_update` filtered by `run_id`; fallback poll `GET runs/{id}` every 2 s when WS not live): stepper Pending → Sending (attempt n) → Verifying (countdown vs `timeout_s`) → terminal; terminal states: VERIFIED green ✓ + latency, FAILED_TIMEOUT amber "device didn't respond — check camera view", FAILED_SERVICE red + HA message, DONE_UNVERIFIED grey ✓ "sent (unverified)"; 409-busy → toast with link to the running run's progress.
5. `RunHistoryDrawer` per appliance: recent runs from events (`kind=verification.update`, terminal only) — action, state, attempts, when.
6. Delete/edit appliance with confirm; `verify_sensor_missing` warnings (issue 23-4) rendered on affected actions with a "fix" link to the editor.
7. Empty state teaches the model in one sentence + "Add appliance" CTA (prereq note: HA configured + at least one sensor for verification).

## Acceptance Criteria
- [ ] vitest: ActionEditor produces exactly the DESIGN §9.1 example JSON from UI interactions (golden serialize test); param toggle round-trip; expectation/sensor compatibility filtering matrix; HA-offline force flow sets `?force=true` and renders warnings.
- [ ] RunProgress state machine rendering driven by a scripted WS message sequence covers all §9.4 states incl. retry increment and busy-409 path (fake timers for countdown).
- [ ] Manual E2E vs stub HA + replay led camera (issue 24's harness, run locally): click power_on → watch Verifying → VERIFIED; kill the "lamp" → FAILED_TIMEOUT after retries; screenshots/screencast in PR.
- [ ] WS-less fallback (WS disabled in devtools) still completes via polling.
- [ ] No dead buttons: every action visible on cards is runnable or disabled-with-reason.

## Validation
CI vitest; recorded manual E2E per above.

## Dependencies
26, 23, 24, 19.

## Non-goals
No macro/scene composition (v2), no scheduling/automations (HA's job), no appliance sharing/export beyond entity export (31).

## Design References
DESIGN §9.1–9.4, §11.1, §7.2; issues 23/24 semantics.

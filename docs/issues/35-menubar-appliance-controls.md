# Implement menu bar appliance controls with verification progress and notifications

## Summary
Implement the appliance section of the menu bar app: action buttons (with param sheets when needed), live verification progress in the menu, and `UserNotifications` on terminal states — completing US-3 ("control the AC from the MacBook, verified").

## Context
Builds on 33/34 (client, WS). The menu bar is where verified control pays off: click, glance, trust the ✓.

## Scope
- `Sources/Appliances/ApplianceListModel.swift`, `ApplianceSection.swift`, `ParamSheet.swift`, `RunTracker.swift`, `Notifications.swift`.

## Detailed Requirements
1. `ApplianceListModel`: fetch appliances on menu open (30 s cache); render appliance submenu per appliance: action rows (verify badge shown when configured).
2. Parameterless action click → dispatch immediately; parameterized → small `ParamSheet` window (text fields per declared param, numeric `inputmode`-style formatting hint, Run/Cancel; remembers last values per action in UserDefaults. v1 rule: store all param values — §9.2 params are appliance settings like temperature, not secrets).
3. `RunTracker`: after 202, track via WS `verificationUpdate` (filtered run_id) with 2 s polling fallback (34's transport state decides); expose per-appliance `RunState` for menu rendering: spinner + state text (`Sending (2/3)…`, `Verifying 12s…`) while the menu is open; only one tracked run per appliance (server enforces via 409 — busy click shows the running state instead of erroring).
4. `Notifications`: request authorization on first run dispatch (not app launch); terminal notifications — VERIFIED: "✓ Living AC · power_on verified (8.2 s)"; FAILED_*: "✗ … failed — check camera/HA" with the reason line; DONE_UNVERIFIED: "sent (unverified)". Clicking a notification opens the Web UI appliances page. Respect denied-authorization (silent, menu still shows outcome for 60 s).
5. Errors: dispatch 4xx/409/transport → inline menu row error text for 10 s + notification only for terminal run failures (no double-noise).
6. All strings centralized (Localizable-ready, English v1 — mirrors web i18n posture).

## Acceptance Criteria
- [ ] XCTest: RunTracker state transitions from scripted WS sequences (happy, retry, timeout, service-fail, busy), notification payload builder matrix, param sheet → §9.2-shaped request body (golden), last-values persistence.
- [ ] Manual vs stub-HA + replay lamp harness: click power_on → menu spinner → VERIFIED notification with latency; forced timeout → failure notification with reason; screenshots/screencast in PR.
- [ ] Busy path: second click during a run shows progress, sends nothing (asserted via stub HA call count).
- [ ] Notification tap opens `<hub>/appliances` in the browser.
- [ ] Authorization-denied path degrades gracefully (manual toggle in System Settings, noted in PR).

## Validation
XCTest in CI; manual E2E per above (reuses issue 24/30 harness).

## Dependencies
33, 34, 23, 24.

## Non-goals
No global hotkeys (v2), no widgets/Shortcuts intents (v2), no sensor-change notifications, no run history UI (Web UI owns it).

## Design References
DESIGN §11.3, §9.2–9.4; issue 24 semantics; ADR-003.

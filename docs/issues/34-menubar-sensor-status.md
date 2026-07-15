# Implement menu bar sensor status view with live updates

## Summary
Implement the sensor section of the menu bar app: latest values per sensor with availability/staleness treatment, fed by the WebSocket stream (ticket flow) with polling fallback — the at-a-glance surface (P-2).

## Context
Builds on the 33 scaffold. WS stability inside `MenuBarExtra` is flagged K5: implement WS-first with an automatic, observable downgrade to 5 s polling.

## Scope
- `Sources/Sensors/SensorListModel.swift` (`@MainActor ObservableObject`), `SensorRowView.swift`, `SensorSection.swift`; `Api/WsClient.swift` (`URLSessionWebSocketTask` wrapper).

## Detailed Requirements
1. `WsClient`: mint ticket (33's client) → connect `ws(s)://…/api/v1/ws?ticket=…` (scheme derived from hub URL); decode the §19 envelope into a Swift enum (`sensorUpdate`, `sensorAvailability`, `cameraStatus`, `verificationUpdate`, `event`, `hello`, `ping`); treat server `ping` as liveness and send the documented client heartbeat `{"type":"ping"}` on a timer/after reconnect (server replies `pong` per issue 19), never an undocumented client `pong`; reconnect with 1→30 s backoff; after 3 consecutive failed connects → switch model to polling mode and retry WS every 5 min.
2. `SensorListModel`: initial `latestReadings()` snapshot, then WS patches; polling mode refetches every 5 s; exposes `[SensorItem]` (id, name, readerType, valueText, confidence, available, ageSeconds, live: Bool) + `transport: .ws/.polling/.down`.
3. `SensorRowView` per reader type: led → colored dot (uses reported color name mapped to system colors, fallback accent) + ON/OFF; sevenseg → monospaced number + unit (— when null); change → "changed Xs ago"/"stable". Unavailable → greyed with reason tooltip; stale (age > 180 s) → amber clock glyph.
4. Menu shows up to 12 sensors (config-free v1 rule: order = server order); >12 → "… and N more (open Web UI)".
5. Value formatting shared helper with unit tests (nil-number, long names truncated with middle-ellipsis at 28 chars, confidence < 0.7 renders "≈" prefix).
6. Transport indicator integrated into the 33 status line ("live" / "polling" / "offline").
7. Energy discipline: WS idle is cheap; polling timer tolerance 1 s; no timers when hub unconfigured.

## Acceptance Criteria
- [ ] XCTest: envelope decoding fixtures for every message type; model patch logic (update replaces the right row; availability greys it; gap/hello triggers snapshot refetch); heartbeat sends client `ping` and accepts server `pong`; WS→polling downgrade after 3 simulated failures; formatting helper matrix.
- [ ] Manual vs live hub + replay cameras: value flips appear ≤ 1 s in WS mode; kill WS route → app degrades to polling within ~15 s and still updates (≤ 5 s cadence); screenshots in PR.
- [ ] 15-sensor hub renders 12 + overflow row.
- [ ] No main-thread stalls (Instruments quick pass note in PR).

## Validation
XCTest in CI; manual smoke per above.

## Dependencies
33, 19, 18.

## Non-goals
No per-sensor pinning/ordering UI (v2), no charts, no notifications (35 handles run notifications; sensor-change notifications are v2).

## Design References
DESIGN §11.3, §7.4, §6.2; DESIGN §16 K5.

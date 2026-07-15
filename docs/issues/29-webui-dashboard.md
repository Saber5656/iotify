# Implement the Web UI dashboard (live tiles, history charts, event feed)

## Summary
Implement the Dashboard page: live sensor tiles fed by WebSocket, per-sensor history modal with Recharts (using downsampled readings), camera status strip, and a recent-events feed — the daily-driver read surface (US-1/US-2).

## Context
This page consumes `readings/latest` (18), WS updates (19), history queries (18), and events (18). It must stay calm: no flicker on reconnect, obvious staleness, graceful empty states.

## Scope
- `web/src/pages/dashboard/`: `DashboardPage`, `SensorTile`, `HistoryModal`, `CameraStrip`, `EventFeed`.

## Detailed Requirements
1. Initial load: `GET /readings/latest` renders tiles and `GET /events?limit=20` renders the feed; then WS `sensor_update`/`sensor_availability` patch state in place and WS `event`/`verification_update` prepends feed entries. `resync` callback (gap marker / reconnect) refetches both latest readings and the recent event window before clearing reconnect state.
2. `SensorTile` per reader type: led → big on/off dot + color name; sevenseg → number + unit (monospace, 1-decimal formatting per value); change → stable/changed with `magnitude` bar and last-change relative time. Common: name, camera link, confidence subtext, availability treatment (greyed + reason when unavailable), staleness dot (amber) when `age_s > 180` (client-side constant = 3× the default 60 s heartbeat; the API contract stays as-is — document the constant in code).
3. Tile click → `HistoryModal`: time-range picker (1h/24h/7d/30d), Recharts line (numeric: value + min/max band from downsample buckets) or state timeline (discrete: colored step chart); loading skeleton; empty-history state; fetch uses `downsample` sized to modal width (~200 buckets).
4. `CameraStrip`: one chip per camera (health badge + name → links to /cameras); hidden when single healthy camera.
5. `EventFeed`: latest 20 events (kind icon, subject link, relative time), live-prepends from WS `event`/`verification_update`, "view all" → `/events` page (simple table version of the feed with kind/time filters — included in this issue).
6. Layout: responsive CSS grid (tiles ≥ 220 px), phone-friendly single column; sidebar collapses (25's layout handles; verify).
7. Reconnect UX: header WS indicator (from 26); while `reconnecting`, tiles keep last values with a subtle banner "live updates paused".
8. All timestamps rendered relative ("12 s ago") with absolute on hover; timezone = browser local (values stored UTC — DESIGN §6.1).

## Acceptance Criteria
- [ ] vitest: tile rendering per reader fixture states (on/off/null-number/unavailable/stale), WS patch logic (update arrives → exactly one tile re-renders — assert via testid text), resync refetches latest readings and recent events on gap/reconnect.
- [ ] HistoryModal renders numeric chart from a 100-bucket fixture incl. min/max band, and step timeline for led fixtures; range picker changes trigger correctly-parameterized fetches (mock asserts `from/to/downsample`).
- [ ] Events page filters by kind and paginates by `limit` (mock-asserted).
- [ ] Manual smoke (replay cameras: led flip + sevenseg count-up): tiles update ≤ 1 s after MQTT sees the same change; screenshots in PR.
- [ ] Empty states: zero sensors → onboarding CTA to /cameras; zero events → quiet placeholder.

## Validation
CI vitest; manual smoke checklist in PR (paired with issue 15's replay scenario).

## Dependencies
26, 18, 19; 28 (sensors exist to display — dev fixture path acceptable).

## Non-goals
No dashboard customization/reordering (v2), no CSV export, no appliance controls on this page (30 owns control UX).

## Design References
DESIGN §11.1, §7.2, §7.4, §6.2/§6.4.

# Implement WebSocket live updates with ticket authentication

## Summary
Implement `POST /api/v1/system/ws-ticket` and `GET /api/v1/ws` per DESIGN §7.1/§7.4: single-use short-TTL tickets, typed push messages fanned out from the event bus, heartbeats, and slow-consumer protection.

## Context
Live updates drive the Web UI dashboard (29), ROI editor test panel (28), CLI `sensor watch` (31), and menu bar app (34). Ticket auth avoids long-lived tokens in URLs (ADR-004-2).

## Scope
- `src/iotify/server/api/ws.py`: ticket mint endpoint, ticket store, WS endpoint, bus-subscription fanout task per connection.

## Detailed Requirements
1. Ticket: 16 random bytes urlsafe; TTL 60 s; single-use (consumed on first WS accept attempt, valid or not); store = in-memory dict with periodic sweep; mint endpoint requires Bearer token; response `{ticket, expires_at_ms}`.
2. `GET /api/v1/ws?ticket=…`: invalid/expired/reused → close with code 4401 before accepting any subscription; valid → accept, send `{"type":"hello","data":{"version":…,"server_ts":…}}`.
3. Push message envelope `{type, ts, data}`; types and payload mapping from bus events:
   - `sensor_update` ← `sensor.state_changed` (+ heartbeat readings do **not** stream; document),
   - `sensor_availability` ← `sensor.availability`,
   - `camera_status` ← `camera.health_changed`,
   - `verification_update` ← `verification.update`,
   - `event` ← anything persisted to the events table not covered above.
4. Heartbeat: server sends `{"type":"ping"}` every 20 s; client may send `{"type":"ping"}` (server replies `pong`); server closes after 60 s without any client frame or successful send.
5. Slow consumer: per-connection outbound queue 256; overflow drops oldest and injects one `{"type":"event","data":{"gap":true}}` marker (client refetches via REST).
6. Multiple concurrent connections supported (≥ 8); each gets an independent bus subscription (issue 09 bus semantics); connection close must cancel the fanout task and unsubscribe (no leaks — assert subscriber count returns to baseline).
7. Message schema documented in `docs/api/ws.md` (create; referenced by clients in issues 26/31/34).

## Acceptance Criteria
- [ ] Ticket flow: mint → connect ok; reuse → 4401; expiry (fake clock) → 4401; connect without ticket → 4401.
- [ ] Replay-camera state change appears as `sensor_update` on 2 concurrent connections within 1 s.
- [ ] Ping/pong + idle-timeout behavior verified with fake clock.
- [ ] Queue overflow injects exactly one gap marker and connection survives.
- [ ] Subscriber-leak assertion passes after 50 connect/disconnect cycles.
- [ ] `docs/api/ws.md` written with every message type + example payloads.

## Validation
`pytest tests/integration/test_ws.py` using httpx-ws or starlette `TestClient` WS support against the booted app.

## Dependencies
16, 09 (bus), 15 (events flowing).

## Non-goals
No client-side subscriptions/filtering (all-events firehose in v1), no compression, no reconnect logic (client concern).

## Design References
DESIGN §7.1, §7.4, §6.5; ADR-004-2.

# Implement REST API: readings history, latest values, and event log

## Summary
Implement `/api/v1/sensors/{id}/readings`, `/api/v1/readings/latest`, and `/api/v1/events` per DESIGN §7.2, exposing the storage-layer queries (issue 04) with strict parameter validation.

## Context
These read-only endpoints power the dashboard charts (29), CLI watch/tail (31), and menu bar glance (34).

## Scope
- `src/iotify/server/api/readings.py`, `events.py` + schemas.

## Detailed Requirements
1. `GET /sensors/{id}/readings?from=&to=&limit=&downsample=`:
   - `from`/`to`: epoch ms; defaults `to=now`, `from=to−24h`; reject `from>to` (422) and ranges > 90 days (422, matches max retention);
   - `limit` default 1000, max 10000; `downsample` = target bucket count 10–2000, mutually exclusive with `limit` honored as documented: when `downsample` set, use repo bucket query (issue 04-4), else raw rows capped by `limit` (newest first);
   - response rows: `{ts, value, confidence}` (+ `{min,max}` per bucket for numeric downsampled).
2. `GET /readings/latest`: array of `{sensor_id, ts, value, confidence, available: bool, age_s}` for every enabled sensor (availability from pipeline state, not DB).
3. `GET /events?kind=&from=&to=&limit=`: kind filter validated against the §6.5 enum (422 otherwise); limit default 100 max 1000; newest first; payload passed through as stored JSON.
4. All three endpoints set `Cache-Control: no-store`; timings logged at debug only.
5. Response size guard: downsampled numeric response for 90 days × 2000 buckets must serialize < 1 MiB (integration-tested with synthetic data).
6. Unknown sensor id → 404 problem+json (consistent with 17).

## Acceptance Criteria
- [ ] Seeded 10k-reading sensor: raw query respects limit+ordering; `downsample=100` returns ≤ 100 buckets with correct min/max (cross-checked in test against numpy).
- [ ] Range/limit/kind validation errors are 422 problem+json with parameter names.
- [ ] `readings/latest` reflects pipeline availability (kill the replay camera → `available:false, age_s` grows).
- [ ] 90-day × 2000-bucket response < 1 MiB.
- [ ] OpenAPI models complete.

## Validation
`pytest tests/integration/test_api_readings_events.py` with seeded DB + live pipeline fixture.

## Dependencies
16, 04, 15.

## Non-goals
No CSV export (v2), no aggregation beyond min/max/last, no WebSocket (19).

## Design References
DESIGN §7.2, §6.1–6.2, §6.5.

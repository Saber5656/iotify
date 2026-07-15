# Implement the stabilizer and the end-to-end sensor pipeline

## Summary
Implement `iotify.sensing.stabilizer` (debounce/hysteresis/heartbeat per DESIGN §6.4) and `iotify.sensing.pipeline` — the orchestrator that consumes fresh frames, runs readers, stabilizes results, persists readings, writes event snapshots, and publishes bus events (DESIGN §10.2).

## Context
This issue turns parts (scheduler, readers, storage, bus) into the product's sensing core. Stabilization quality is a headline differentiator (research takeaway 3): no flapping states, no confident garbage.

## Scope
- `src/iotify/sensing/stabilizer.py`: `Stabilizer` per sensor — `update(reading, now_ms) -> StabilizerOutput` where output ∈ `{NoChange, StableChange(value, confidence), Heartbeat(value), BecameUnreadable(reason), BecameReadable}`.
- `src/iotify/sensing/pipeline.py`: `SensorPipeline` — `start(scheduler, db, bus)`, `stop()`, hot `add/remove/update_sensor(row)`, `test_read(sensor_id, debug: bool) -> Reading` (on-demand for API), calibration-image cache management.

## Detailed Requirements
### Stabilizer (pure, fake-clock-tested)
1. Ring buffer of last `window` readings (default 5). Discrete values (led state+color, change state): report `StableChange` when ≥ `agree` (default 3) of the window agree on a value different from the last reported value.
2. Numeric (`sevenseg.number`): candidate = median of window; `max_jump` (when set) rejects candidates jumping more than max_jump from last reported (outlier guard) unless the full window agrees; `deadband` suppresses |Δ| < deadband; report median as `StableChange`.
3. `min_report_interval_s` rate-limits `StableChange` (coalesce to latest).
4. `heartbeat_interval_s` (default 60): re-emit current stable value as `Heartbeat` when no change reported within the interval (drives MQTT freshness + history density).
5. Unreadability: `window` consecutive readings with `confidence < min_confidence` (reader-specific; default 0.5 when reader config lacks it) → `BecameUnreadable(reason)` once; first good stable value after → `BecameReadable` then `StableChange`.
### Pipeline
6. Subscribes to `scheduler.fresh_frames()`; for each frame, processes that camera's enabled sensors on the `analyze` executor (DESIGN §4.2); per-sensor serialization guaranteed (one in-flight read per sensor; skip frame if busy — never queue).
7. Per sensor: `crop_roi` (ROI out of bounds → availability false with `roi_out_of_bounds`) → reader instance (created via registry at add/update; calibration crops loaded from storage into `ReadContext.calibration`) → stabilizer.
8. Output handling:
   - `StableChange` → `insert_reading` + bus `sensor.state_changed {value, confidence, previous}`;
   - `Heartbeat` → `insert_reading` only (no state_changed event);
   - every persisted reading (both cases above) additionally publishes bus `sensor.reading_persisted {value, confidence, ts}` (bus-only kind, not written to the events table — consumed by the MQTT publisher, issue 20);
   - `BecameUnreadable/Readable` → bus `sensor.availability {available, reason}`;
   - change-reader `raw.snapshot_requested` → JPEG of the full ROI saved to `<data>/snapshots/change/<sensor_id>/<ts>.jpg` (quality 80), path embedded in the `sensor.state_changed` payload; files subject to retention (issue 04).
9. Camera health events: camera OFFLINE → all its sensors get availability false (`camera_offline`); ONLINE recovery → readers/stabilizers reset (fresh window, change-reader `_prev` cleared).
10. `test_read` runs synchronously on the latest cached frame with `debug=True` support, bypassing the stabilizer, never persisting, and never mutating the live per-sensor reader/stabilizer state. Use a disposable reader instance or snapshot/restore reader state around the read so change-reader `_prev` and cooldown state cannot perturb the scheduled pipeline.
11. Sensor CRUD hot-reload: update replaces reader+stabilizer atomically; delete stops processing before repo cascade delete (no reads on deleted sensors).
12. Metrics counters (in-memory, exposed via §7.2 `/system/info` later): frames processed, reads, read errors, per-sensor last_read_ts.

## Acceptance Criteria
- [ ] Flapping input (on/off alternating frames) produces zero `StableChange` events; solid 3-of-5 agreement produces exactly one.
- [ ] Numeric outlier (26.5, 26.5, 88.8, 26.5…) with `max_jump=5` never reports 88.8.
- [ ] Heartbeat readings persist at the configured cadence without state_changed events.
- [ ] 5 consecutive low-confidence reads → exactly one availability-false event with reason; recovery emits readable + state.
- [ ] End-to-end (replay camera → led sensor → bus): scripted lamp-on sequence yields the expected single state_changed with persisted reading (integration test, no network).
- [ ] Change-reader snapshot file written once per event, path in payload, deleted by retention test.
- [ ] Camera OFFLINE cascades availability to its sensors; recovery resets stabilizer windows (asserted via no stale-value report).
- [ ] `test_read` on a change sensor does not advance the live reader `_prev`/cooldown state (assert scheduled next frame is identical with and without a prior debug read).

## Validation
`pytest tests/unit/sensing/test_stabilizer.py` (fake clock, ≥ 15 cases) + `tests/integration/test_pipeline_replay.py` (replay camera + tmp DB + real bus; marked integration, runs in CI).

## Dependencies
04, 09, 10, 11, 12, 13, 14.

## Non-goals
No MQTT/WS fanout (20/19 subscribe to the bus), no REST endpoints (17/18), no multi-frame readers.

## Design References
DESIGN §6.4, §10.2, §4.2, §6.5; research takeaway 3.

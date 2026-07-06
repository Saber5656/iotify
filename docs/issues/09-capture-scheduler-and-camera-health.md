# Implement the capture scheduler and camera health state machine

## Summary
Implement `iotify.cameras.scheduler` and `iotify.cameras.health`: one capture thread per enabled camera polling at `poll_interval_s`, a latest-frame cache, reconnect with exponential backoff, and the ONLINE/DEGRADED/OFFLINE health state machine emitting bus events.

## Context
This is the heartbeat of the hub (DESIGN §10.1). Downstream, the sensor pipeline (issue 15) consumes fresh frames and the API (17) serves snapshots from the cache. Also introduces the event bus used product-wide.

## Scope
- `src/iotify/events/bus.py`: minimal async pub/sub — `EventBus.publish(kind: str, subject_id: str | None, payload: dict)`, `subscribe(kinds: set[str] | None) -> AsyncIterator[Event]` (bounded per-subscriber queues, drop-oldest + `dropped` counter); `Event` dataclass `{kind, subject_id, payload, ts_ms}`.
- `src/iotify/cameras/health.py`: `CameraHealth` enum (`STARTING/ONLINE/DEGRADED/OFFLINE`) + transition function per DESIGN §10.1 diagram.
- `src/iotify/cameras/scheduler.py`: `CaptureScheduler` — `start(cameras)`, `stop()`, `add/remove/update_camera(row)` (hot reconfig used by CRUD API), `latest(camera_id) -> Frame | None`, `fresh_frames() -> AsyncIterator[(camera_id, Frame)]` (feeds pipeline), `health(camera_id)`, `health_map()`.

## Detailed Requirements
1. One daemon thread per enabled camera: loop `{read_frame → cache[camera_id] = frame → sleep to next tick}`; tick period = `poll_interval_s`, measured from loop start (no drift accumulation).
2. Error handling per iteration: taxonomy errors increment failure streak; scheduler never lets a camera exception escape the thread.
3. Health transitions (evaluated on every tick and error):
   - STARTING → ONLINE on first good frame; STARTING → OFFLINE after open fails 3×.
   - ONLINE → DEGRADED when now − last_frame_ts > 3×interval.
   - DEGRADED → ONLINE on fresh frame; DEGRADED → OFFLINE when gap > 10×interval or hard error (`CameraAuthFailed`).
   - OFFLINE → STARTING per reconnect backoff: 1, 2, 4, … capped 60 s, ±20 % jitter; `CameraAuthFailed` uses fixed 60 s (no point hammering).
4. Every health change publishes `camera.health_changed` `{state, detail}` on the bus exactly once per transition (no repeats while stable).
5. `fresh_frames()` delivers each cached frame at most once to the pipeline (per-camera monotonic frame counter), bridged thread→async via `loop.call_soon_threadsafe`.
6. `stop()` joins all threads ≤ 5 s (sources' `close()` called), then emits `system.stopping`.
7. `update_camera` (interval/url/enabled change) restarts only that camera's thread; disabled camera → thread stopped, health map entry removed, cache cleared.
8. Frame cache holds exactly one frame per camera (memory budget: DESIGN §10.3).

## Acceptance Criteria
- [ ] With a replay camera at 0.5 s interval, `fresh_frames()` yields ≥ 8 distinct frames in 5 s, no duplicates.
- [ ] Simulated read failures (fake source) drive ONLINE→DEGRADED→OFFLINE at exactly the 3×/10× thresholds (fake clock).
- [ ] Reconnect backoff sequence observed as 1,2,4,…60 s (fake clock; jitter bounds asserted).
- [ ] Exactly one `camera.health_changed` event per transition.
- [ ] `stop()` returns < 5 s with 4 cameras running; no thread leaks (`threading.enumerate` before/after).
- [ ] Hot `update_camera` interval change takes effect without touching other cameras' threads.

## Validation
`pytest tests/unit/cameras/test_scheduler.py test_health.py tests/unit/events/test_bus.py` with fake sources + fake clock; 30 s soak test with 2 replay cameras marked `@pytest.mark.slow`.

## Dependencies
06 (interface, replay); 03 (logging); 04 (CameraRow). 07/08 plug in transparently.

## Non-goals
No sensor analysis (15), no persistence of health (events only), no adaptive frame-rate.

## Design References
DESIGN §10.1 (state machine), §4.2 (threading model), §6.5 (events), §10.3 (budgets).

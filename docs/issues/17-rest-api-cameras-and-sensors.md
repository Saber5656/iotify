# Implement REST API: camera and sensor resources (CRUD, snapshot, test, calibrate)

## Summary
Implement `/api/v1/cameras*` and `/api/v1/sensors*` routers per DESIGN §7.2: CRUD with strict validation, live snapshot/preview JPEG endpoints, connectivity test, on-demand test-read, and calibration capture.

## Context
These endpoints are the contract for the Web UI (27/28), CLI (31), and entity import/export. They bridge HTTP to repos (04), scheduler (09), and pipeline (15) hot-reload hooks.

## Scope
- `src/iotify/server/api/cameras.py`, `sensors.py`; pydantic request/response schemas in `src/iotify/server/api/schemas.py`.

## Detailed Requirements
### Cameras
1. `POST /cameras` body: `{id, name, source_type, url?, device_index?, username?, password?, poll_interval_s?, rotation?, enabled?}`. Validation: id regex §7.3 + uniqueness (409 on duplicate); scheme allowlist per source_type (`rtsp:` for rtsp; `http/https` for mjpeg/snapshot; filesystem path for replay; none for usb); reject URLs containing userinfo (`user:pass@`) with a pointer to the username/password fields; `device_index` required iff usb.
2. Responses **never include `password`**; field `has_password: bool` instead. `PUT` semantics: omitted `password` keeps existing; explicit `null` clears it.
3. CRUD calls scheduler hooks: create+enabled → `add_camera`; update → `update_camera`; delete → `remove_camera` then repo delete (cascade removes sensors → pipeline `remove_sensor` for each, order: pipeline first, then DB).
4. `GET /cameras` list + `GET /cameras/{id}` include `health` (from scheduler) and `sensor_count`.
5. `GET /cameras/{id}/snapshot?fresh=false`: cached frame → JPEG (quality 85), `Cache-Control: no-store`; `fresh=true` forces a synchronous `read_frame` (10 s timeout budget → 504 problem+json on timeout); 503 when camera OFFLINE and no cache; 404 unknown id.
6. `POST /cameras/{id}/test`: run open+read against current stored config out-of-band (not disturbing the scheduler thread); returns `{ok, health_detail, latency_ms, frame_size}` or taxonomy-mapped failure `{ok:false, error:"camera_auth_failed"|…}` — never 5xx for camera-side failures.
### Sensors
7. `POST /sensors` body: `{id, name, camera_id, reader_type, roi:{x,y,w,h}, reader_config?, stabilizer_config?, ha_device_class?, unit?, enabled?}`. Validation: camera exists; ROI within the camera's last known frame bounds when a frame is cached (else accept with `warnings:["roi_unverified"]` in response); `reader_config`/`stabilizer_config` validated via issue-11 `validate_reader_config` (422 with field-level errors).
8. CRUD → pipeline hooks (`add/update/remove_sensor`); response includes `missing_calibration: [..]` (issue 11 helper) so the UI can prompt.
9. `GET /sensors/{id}/preview`: latest ROI crop as JPEG; 503 when no frame.
10. `POST /sensors/{id}/test-read?debug=true|false`: pipeline `test_read`; response `{value, confidence, raw}` with `raw.debug_images: {stage: base64jpeg}` when debug (cap total response 4 MiB; downscale debug images to ≤ 320 px wide).
11. `POST /sensors/{id}/calibrate` body `{label: "baseline_off"|"baseline_on"|"reference"}`: crops current frame ROI, saves PNG under `<data>/snapshots/calibration/<sensor_id>/<label>.png` (overwrite same label), records via repo, returns the record; 503 no frame; pipeline calibration cache invalidated.
12. Entity lifecycle bus events: sensor delete/disable emits `sensor.deleted` (subject = sensor id, payload `{}`); camera delete emits one `sensor.deleted` per cascaded sensor. Consumed by MQTT (issue 20) to clear retained topics and by discovery (issue 21).
13. Pagination: none in v1 (entity counts are small); document the decision in the router docstring.

## Acceptance Criteria
- [ ] Full CRUD happy paths + every validation rule above covered by API tests (httpx ASGI client, replay cameras).
- [ ] Password never appears in any response body or log line (grep assertion over test transport + caplog).
- [ ] Snapshot/preview return decodable JPEGs (`cv2.imdecode` in test); `fresh=true` timeout path returns 504 problem+json.
- [ ] Deleting a camera with 2 sensors: pipeline stops reads first, DB cascade removes rows, snapshots cleaned (issue 04 rule), scheduler thread gone.
- [ ] `test-read` debug response ≤ 4 MiB with 3 debug stages on a 1080p frame.
- [ ] Calibrate creates the file (mode inherits 0700 dir), record row, and clears `missing_calibration` on next GET.
- [ ] OpenAPI schema includes all routes with correct models (snapshot endpoints marked `application/octet-stream`/`image/jpeg`).

## Validation
`pytest tests/integration/test_api_cameras.py test_api_sensors.py` against a booted test app (issue 16 fixtures).

## Dependencies
16 (app/auth), 09, 15, 04, 11.

## Non-goals
No readings/events endpoints (18), no HA proxy endpoints (23), no UI.

## Design References
DESIGN §7.2–7.3, §6.1, §12.3-2/3.

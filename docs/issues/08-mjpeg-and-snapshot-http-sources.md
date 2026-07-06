# Implement MJPEG stream and HTTP snapshot camera sources

## Summary
Implement `MjpegSource` (multipart MJPEG over HTTP) and `SnapshotSource` (GET a JPEG/PNG per poll) with httpx, Basic/Digest auth, and strict size/type/time limits — the ESP32-CAM-class ingestion path.

## Context
ESP32-CAM and phone-camera apps expose `http://…/stream` (MJPEG) or `http://…/jpg` (snapshot). These parse *attacker-influenceable* bytes, so input caps are security requirements (DESIGN §12.2 T3), not niceties.

## Scope
- `src/iotify/cameras/mjpeg.py`, `src/iotify/cameras/snapshot.py`; registry entries `mjpeg`, `snapshot`; `httpx` runtime dep (rationale line).

## Detailed Requirements
1. Shared HTTP client factory `iotify.cameras._http.build_client(camera) -> httpx.Client`: timeout budget `connect=5s, read=5s, total=10s`; auth strategy: if `camera.username` is set, send Basic preemptively; on a 401 response carrying a Digest challenge, retry exactly once with `httpx.DigestAuth`; `verify=True` default for https; redirects disabled (`follow_redirects=False`) — a redirecting camera is suspicious, raise `CameraUnavailable(detail="redirect refused")`.
2. **SnapshotSource.read_frame**: GET `camera.url`; require `Content-Type` starting `image/jpeg` or `image/png`; enforce `Content-Length`/streamed size ≤ **8 MiB** (DESIGN §12.2 T3) — abort mid-body if exceeded → `CameraDecodeError(detail="snapshot too large")`; decode via `cv2.imdecode`; decode failure → `CameraDecodeError`.
3. **MjpegSource**: `open()` starts a streaming GET expecting `multipart/x-mixed-replace`; parse boundary from Content-Type header (quoted or bare); `read_frame()` reads parts until a complete JPEG part is assembled; per-part size cap 8 MiB; malformed part → skip with counter, 3 consecutive malformed → `CameraDecodeError`; connection drop → `CameraUnavailable`.
4. Status mapping: 401/403 → `CameraAuthFailed`; 404/5xx → `CameraUnavailable(status)`; timeout → `CameraTimeout`.
5. URL scheme allowlist `http|https` asserted here too (defense in depth vs API-layer validation).
6. `close()` closes stream + client, idempotent.
7. Tests use a local `pytest`-launched ASGI/threaded HTTP fixture server (no network): endpoints for jpeg ok, wrong content-type, oversize body (streamed), 401-basic, 401-digest-then-ok, redirect, MJPEG stream of 3 frames + malformed part injection.

## Acceptance Criteria
- [ ] All fixture-server cases above mapped to the exact taxonomy class stated.
- [ ] Oversize body aborts before buffering more than 8 MiB + one chunk (assert via server-side sent-bytes counter).
- [ ] MJPEG yields 3 sequential distinct frames, skips one malformed part, errors after 3 consecutive malformed.
- [ ] Redirect (302) refused with `CameraUnavailable`.
- [ ] No credential material in errors/logs (test asserts).
- [ ] mypy strict passes.

## Validation
`pytest tests/unit/cameras/test_mjpeg.py test_snapshot.py` against the in-process fixture server; manual ESP32-CAM smoke documented in PR if hardware available (optional).

## Dependencies
06.

## Non-goals
No RTSP/USB (07), no mDNS discovery, no HTTPS cert pinning, no reconnect policy (09).

## Design References
DESIGN §12.2 T3 (size/type caps), §7.3 (scheme allowlist), §10.1.

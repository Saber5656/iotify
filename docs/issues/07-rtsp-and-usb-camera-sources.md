# Implement RTSP and USB camera sources

## Summary
Implement `RtspSource` and `UsbSource` on top of OpenCV `VideoCapture`, with credential handling, timeouts, staleness detection, and reconnect-friendly error mapping.

## Context
RTSP IP cameras and USB webcams are the two primary real sources (DESIGN §3.1-2). They must fail into the issue-06 error taxonomy so the scheduler's health state machine (issue 09) can drive reconnects.

## Scope
- `src/iotify/cameras/rtsp.py` (`RtspSource`), `src/iotify/cameras/usb.py` (`UsbSource`); registry entries for `rtsp` and `usb`.

## Detailed Requirements
1. **RTSP**: build URL from `camera.url`; if `camera.username` set, inject userinfo credentials only when the URL has none (already-embedded userinfo in `url` is rejected at API layer, issue 17 — here, assert-and-raise `ValueError`). Use `cv2.VideoCapture(url, cv2.CAP_FFMPEG)` with env `OPENCV_FFMPEG_CAPTURE_OPTIONS` set for TCP transport (`rtsp_transport;tcp|stimeout;5000000`) — set via `os.environ` at module import guarded to not clobber an existing value; document override.
2. RTSP `open()`: `isOpened()` false → `CameraUnavailable`; a 401/auth-shaped failure cannot be distinguished by OpenCV reliably → map to `CameraUnavailable` with detail `"open failed (check URL/credentials)"`; never include the password in `detail` (username allowed).
3. RTSP `read_frame()`: `grab()` loop to drain buffered frames (grab up to 5, retrieve last) so readings reflect *now*, not a stale buffer; `read()` false → `CameraTimeout`.
4. **USB**: `cv2.VideoCapture(camera.device_index)` (macOS AVFoundation / Linux V4L2 default backends); `device_index` required for `usb` type (validated in API layer; here raise `ValueError` if None). Set capture resolution only if defaults fail; never force.
5. Both: `close()` releases capture and is idempotent; `read_frame` after `close` raises `CameraUnavailable`.
6. Both apply shared rotation helper (issue 06).
7. No blocking call may exceed ~10 s worst case (document ffmpeg `stimeout` covers RTSP; USB reads are local).
8. Unit tests must not require hardware/network: wrap `cv2.VideoCapture` behind a module-level factory `_capture_factory` monkeypatchable in tests; simulate open-fail, read-fail, and success with a fake.

## Acceptance Criteria
- [ ] Fake-backed tests: open success/failure, read timeout mapping, buffer-drain logic (last grabbed frame wins), close idempotency — all green without devices.
- [ ] Credentials never appear in any exception message or log (test asserts).
- [ ] `usb` without `device_index` and `rtsp` with userinfo-in-URL raise `ValueError` with clear messages.
- [ ] Manual smoke procedure documented in the PR description: one real RTSP cam or `ffmpeg -re -stream_loop` local RTSP server (mediamtx) + one USB cam on macOS, each producing a frame via a 5-line snippet.
- [ ] mypy strict passes.

## Validation
`pytest tests/unit/cameras/test_rtsp.py test_usb.py` (fakes); manual smoke per above recorded in PR (output pasted, no images committed).

## Dependencies
06.

## Non-goals
No ONVIF discovery (v2), no MJPEG/snapshot (08), no reconnect loops (09 owns retry), no transcoding.

## Design References
DESIGN §3.1-2, §10.1, §12.2 T3 (decode failures quarantine), §16 K2.

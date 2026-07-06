# Define the CameraSource interface, error taxonomy, registry, and replay source

## Summary
Implement `iotify.cameras.base` (the `CameraSource` contract and error taxonomy), a source-type registry, and the file-based `replay` source used by tests, demos, and the E2E suite.

## Context
All camera access flows through one interface so the scheduler (issue 09) and tests are source-agnostic (DESIGN §3.1-2, §4.3). The replay source is deliberately first: every downstream issue tests against it without hardware.

## Scope
- `src/iotify/cameras/base.py`:
  ```python
  class Frame(NamedTuple):
      image: np.ndarray  # BGR uint8
      ts_ms: int

  class CameraSource(ABC):
      def __init__(self, camera: CameraRow): ...
      @abstractmethod
      def open(self) -> None: ...
      @abstractmethod
      def read_frame(self) -> Frame: ...   # blocking, raises CameraError
      @abstractmethod
      def close(self) -> None: ...
  ```
- Error taxonomy (all subclass `CameraError(Exception)` with `camera_id`, `detail`): `CameraUnavailable`, `CameraAuthFailed`, `CameraTimeout`, `CameraDecodeError`.
- `src/iotify/cameras/registry.py`: `create_source(camera: CameraRow) -> CameraSource` mapping `source_type` → class; unknown type → `ValueError`. Registration via explicit dict (no entry-point magic in v1).
- `src/iotify/cameras/replay.py`: `ReplaySource` — `url` points to a directory of images (sorted lexicographically, looped) or a video file (looped via OpenCV `VideoCapture`); each `read_frame` returns the next frame; `fps` semantics: one frame per `read_frame` call (pacing is the scheduler's job).
- numpy + opencv-python-headless added to runtime deps (rationale line per DESIGN §12.3-5).

## Detailed Requirements
1. `read_frame` must always return BGR uint8 3-channel; grayscale inputs are converted; alpha stripped.
2. Rotation (`camera.rotation` ∈ {0,90,180,270}) is applied inside `read_frame` (all sources inherit shared helper `apply_rotation`).
3. Replay directory mode accepts `.jpg/.jpeg/.png` only; empty dir → `CameraUnavailable` at `open()`.
4. Replay path validation: absolute path or repo-relative; must exist at `open()`; no scheme.
5. Unreadable/corrupt image file → `CameraDecodeError` (not a crash), source advances past it on next call.
6. Every error carries `camera_id` and a human-readable `detail` safe to log (no credentials — DESIGN §12.3-2).
7. Type hints complete; no asyncio in this module (sources are blocking by contract; threading handled by scheduler).

## Acceptance Criteria
- [ ] `create_source` maps only *implemented* types (in this issue: `replay`). Unknown or not-yet-implemented types raise `ValueError` whose message lists the currently supported types. Issues 07/08 extend the registry.
- [ ] Replay over a 3-image directory yields frames in name order and loops (frame 4 == frame 1 content).
- [ ] Corrupt file in the middle yields `CameraDecodeError` once, then continues with the next image.
- [ ] Rotation 90/180/270 verified via pixel assertions on an asymmetric test image.
- [ ] Video-file replay yields ≥ 2 distinct frames from a 1 s test clip and loops at EOF.

## Validation
`pytest tests/unit/cameras/test_replay.py` with fixtures under `tests/fixtures/images/replay_basic/` (3 tiny PNGs + 1 corrupt file + 1 tiny mp4 ≤ 50 KB).

## Dependencies
01, 02, 03, 04 (CameraRow).

## Non-goals
No network sources (07/08), no scheduling/health (09), no async wrappers.

## Design References
DESIGN §4.3, §10.1–10.2; ADR-001 (replay as first-class test source); DESIGN §14 (fixture strategy).

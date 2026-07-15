# Implement the generic change-detection reader

## Summary
Implement `ChangeReader` (`reader_type="change"`): frame-differencing against a rolling-previous or fixed-baseline reference with blur, pixel/area thresholds, and cooldown semantics, per DESIGN §6.3 — the catch-all "did anything happen here" sensor (US-4).

## Context
Unlike led/sevenseg, change detection is inherently temporal: it compares against a reference image. The reference lives in reader-owned state *keyed per sensor and managed by the pipeline*, and the cooldown suppresses event storms.

## Scope
- `src/iotify/sensing/readers/change.py` (`ChangeReader`, registered as `change`); sequence fixtures under `tests/fixtures/images/change/sequences/`.

## Detailed Requirements
1. Exception to the "stateless" rule (issue 11) — codify it: `ChangeReader` holds `_prev: np.ndarray | None` and `_last_changed_ts: int`; the pipeline guarantees one reader instance per sensor and single-threaded calls per sensor (issue 15 enforces). Document this narrow exception in `readers/base.py`.
2. Algorithm per `read(image, ctx)`:
   a. gray → gaussian blur (`blur_sigma`),
   b. reference = `fixed_baseline` (calibration image `reference`, required) or rolling previous frame (`rolling_previous`, default; first call → `stable` with magnitude 0 and prev initialized),
   c. `absdiff` → count pixels > `pixel_threshold` → `magnitude` = changed fraction (0..1),
   d. `changed` iff magnitude ≥ `area_threshold` **and** `now_ms - _last_changed_ts >= cooldown_s * 1000` (cooldown consumes the trigger: during cooldown report `stable` but still update magnitude),
   e. rolling mode updates `_prev` every call *after* diffing.
3. `ctx.now_ms` comes from `ReadContext` (issue 11); pipeline injects it; tests use fake clocks — readers never call `time.time()` directly, keeping determinism.
4. `save_snapshot=true`: the reader does **not** write files (I/O-free contract); it sets `raw={"snapshot_requested": true, …}`. The pipeline (issue 15) persists the triggering frame under `<data>/snapshots/change/` and embeds the path in the event payload. This issue only sets the flag and documents that contract.
5. Confidence: `min(1.0, magnitude / (2*area_threshold))` for `changed`; `1 - magnitude/area_threshold` clipped to [0.5,1] for `stable` well below threshold.
6. `raw`: `{magnitude, threshold: area_threshold, cooldown_remaining_s}`; remaining cooldown is calculated in milliseconds and converted back to seconds only for this reported field.

## Acceptance Criteria
- [ ] Sequence test (mailbox-style 6-frame fixture): exactly one `changed` at the change frame, `stable` elsewhere, with rolling reference.
- [ ] Cooldown 30 s (fake clock): second change 10 s later reports `stable` with `cooldown_remaining_s=20`; change after expiry reports `changed`.
- [ ] Fixed-baseline mode: missing `reference` calibration → `raw.error="missing_calibration:reference"`.
- [ ] Slow lighting drift (synthetic brightness ramp ≤ pixel_threshold per frame) never triggers in rolling mode.
- [ ] First-call behavior: `stable`, magnitude 0.
- [ ] mypy strict; deterministic with fake clock.

## Validation
`pytest tests/unit/sensing/test_change_reader.py` with generated sequences (reuse the issue-10 generator for a moving-square sequence).

## Dependencies
10, 11.

## Non-goals
No object classification, no motion tracking, no zone masks (rectangular ROI only), no event snapshot writing (pipeline's job, issue 15).

## Design References
DESIGN §6.2/§6.3 (change), §10.2; ADR-004-7 (snapshot retention).

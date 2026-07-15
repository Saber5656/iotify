# Implement ROI extraction, preprocessing utilities, and the golden-image fixture corpus

## Summary
Implement `iotify.sensing.preprocess` (ROI crop, bounds handling, color/gray/HSV conversions, normalization, deskew helper) and establish the versioned golden-image fixture corpus + comparison helpers that all reader issues (12–14) build on.

## Context
Readers are pure functions over preprocessed ROI images (DESIGN §10.2). Centralizing preprocessing keeps readers small and makes the fixture corpus (DESIGN §14) reusable and consistent.

## Scope
- `src/iotify/sensing/types.py`: `Roi(x, y, w, h)` dataclass; `Reading(value: dict, confidence: float, raw: dict | None)`; `RoiOutOfBoundsError`.
- `src/iotify/sensing/preprocess.py`:
  - `crop_roi(frame: np.ndarray, roi: Roi) -> np.ndarray` (validates bounds against the frame; raises `RoiOutOfBoundsError`)
  - `to_gray(img)`, `to_hsv(img)`, `normalize_brightness(gray) -> np.ndarray` (CLAHE, clip 2.0, tile 8×8)
  - `binarize(gray, invert: bool) -> np.ndarray` (Otsu)
  - `deskew_min_area(binary) -> tuple[np.ndarray, float]` (rotate by `cv2.minAreaRect` angle when |angle| ≤ 15°, else no-op; returns (image, applied_angle))
- Fixture corpus scaffolding: `tests/fixtures/images/README.md` (naming convention, licensing note: only self-made/CC0 images), directories `led/{on,off,colors,glare}/`, `sevenseg/{clean,glare,skew}/`, `change/sequences/`, populated with an initial set (≥ 6 led, ≥ 10 sevenseg covering digits 0–9, ≥ 1 sequence of ≥ 4 frames). Synthetic renders are acceptable and preferred for the initial set; a tiny generator script `tests/fixtures/generate_synthetic.py` (7-seg renderer with configurable digits/skew/noise; LED disc renderer) makes the corpus reproducible.
- `tests/helpers/images.py`: `load_fixture(relpath)`, `assert_image_close(a, b, max_mean_abs_diff)`.

## Detailed Requirements
1. All functions accept/return numpy uint8 arrays; shapes documented in docstrings; no I/O inside preprocess functions.
2. `crop_roi` copies (no views) so readers can mutate safely.
3. Deskew must be a no-op for angles > 15° (avoid destroying portrait ROIs; the API-layer ROI editor owns gross rotation).
4. Synthetic 7-seg generator renders the standard 7-segment geometry per digit with parameters: digit string (incl. `-` and `.`), on/off colors, skew angle, gaussian noise σ, glare ellipse on/off. Deterministic via seed.
5. Fixture files ≤ 100 KB each (pre-commit size budget); PNG preferred.
6. Every helper has unit tests incl. edge cases: 1×1 ROI, ROI touching frame edge, ROI outside frame, already-gray input.

## Acceptance Criteria
- [ ] `crop_roi` bounds behavior verified (inside ok / edge ok / outside raises with sensor-actionable message).
- [ ] `binarize`+`deskew_min_area` on a synthetic 10°-skewed 7-seg render yields applied_angle within ±2° of −10.
- [ ] Generator is deterministic (same seed → byte-identical PNG) and documented in the fixtures README.
- [ ] Corpus present with the minimum counts above; all ≤ 100 KB; README states provenance/licensing rule.
- [ ] mypy strict + `make test` green.

## Validation
`pytest tests/unit/sensing/test_preprocess.py` (≥ 15 cases); run the generator twice and `diff` outputs for determinism.

## Dependencies
01–04, 06 (Frame type/np dependency present).

## Non-goals
No readers (12–14), no stabilizer (15), no perspective (4-point) correction — rectangular ROI + small deskew only in v1.

## Design References
DESIGN §10.2, §14 (fixture strategy), §6.3.

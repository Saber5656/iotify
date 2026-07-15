# Implement the LED/lamp state reader

## Summary
Implement `LedReader` (`reader_type="led"`): detect lamp on/off (and coarse color) inside the ROI by comparing brightness against a captured `baseline_off` calibration image, per DESIGN §6.2/§6.3.

## Context
The lamp reader is the cheapest, highest-value reader (washer done-lamp, router error LED) and the default verification sensor for verified control (US-1, US-3).

## Scope
- `src/iotify/sensing/readers/led.py` (`LedReader`, registered as `led`); fixture additions under `tests/fixtures/images/led/`.

## Detailed Requirements
1. **Brightness mode** (`mode="brightness"`, requires `baseline_off` calibration crop of the same ROI):
   - Convert current ROI and baseline to HSV; compute per-pixel V delta = `clip(V_now - V_base, 0, 255)/255`.
   - Focus metric: mean of the top 20 % brightest-delta pixels (`p80` mask) — robust to a small LED inside a larger ROI.
   - `state = "on"` iff metric ≥ `on_threshold` (default 0.25); `brightness` = metric (0..1, rounded 2dp).
   - Confidence: `min(1, |metric − on_threshold| / on_threshold)` scaled to 0.5–1.0 band when clearly on/off; ≤ 0.5 near the threshold.
2. **Color mode** (`mode="color"`, no baseline required): pixels with `(S ≥ 80 and V ≥ 100) OR (S < 80 and V ≥ 200)` form the lit mask so white LEDs count as lit; if lit-mask fraction < 2 % → `state="off"`, color null. Else `state="on"` and `color` = argmax over hue-bin ranges: red (H<10 or H≥170), orange (10–22), yellow (22–35), green (35–85), blue (85–130), white (S<80 & V≥200 fallback bin). Only bins listed in `color_bins` config compete.
3. Missing required calibration → `Reading(confidence=0, raw={"error":"missing_calibration:baseline_off"})` (pipeline surfaces availability per issue 11 contract).
4. Baseline/ROI size mismatch (ROI edited after calibration) → same missing-calibration error path with reason `stale_calibration`.
5. `raw` debug payload: `{metric, threshold, lit_fraction, hue_histogram(12 bins)}` — powers the UI test-read panel (issue 28).
6. Deterministic; latency budget < 20 ms on a 640×480 ROI (DESIGN §10.3) — add a non-gating perf test that logs the measured time.

## Acceptance Criteria
- [ ] Golden tests: ≥ 6 on/off pairs (incl. 1 glare case) classified correctly in brightness mode with default threshold.
- [ ] Color mode classifies red/green/blue/orange/white synthetic LEDs correctly and returns `off` for the dark frame.
- [ ] Threshold-adjacent case yields confidence ≤ 0.5.
- [ ] Missing/stale calibration cases return the exact `raw.error` strings above.
- [ ] Reading shape passes `validate_reading_shape("led", …)` for every test output.
- [ ] Accuracy gate: 100 % on the committed led corpus (it is small and curated; regressions block).

## Validation
`pytest tests/unit/sensing/test_led_reader.py`; extend corpus with any newly discovered failure case (regression ratchet, DESIGN §14).

## Dependencies
10, 11.

## Non-goals
No blink/temporal detection (v2), no multi-LED-in-one-ROI (one sensor per lamp), no auto-threshold learning.

## Design References
DESIGN §6.2/§6.3 (led), §10.2–10.3, §14; research/prior-art.md takeaway 3.

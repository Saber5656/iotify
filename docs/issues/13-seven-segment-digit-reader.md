# Implement the seven-segment digit display reader

## Summary
Implement `SevensegReader` (`reader_type="sevenseg"`): a classical-CV pipeline (threshold → deskew → digit segmentation → 7-zone sampling → decode) that turns a display ROI into a number, per DESIGN §6.2/§6.3.

## Context
Reading numeric panels (water heater temperature, scales, meters) is the highest-utility sensor (US-2) and feeds numeric verification expectations (§9.3). Prior art (ssocr, AI-on-the-edge-device) shows classical CV suffices when the ROI is tight; ML fallback is the K1 contingency, not this issue.

## Scope
- `src/iotify/sensing/readers/sevenseg.py` (`SevensegReader`, registered as `sevenseg`); corpus additions under `tests/fixtures/images/sevenseg/`.

## Detailed Requirements
1. Pipeline stages (each returning intermediates for `raw` debug):
   a. gray → `normalize_brightness` (CLAHE) → `binarize(invert=config.invert)` (Otsu),
   b. `deskew_min_area` (≤ 15°),
   c. morphological close (3×3, 1 iter) to bridge segment gaps,
   d. digit segmentation: connected components filtered by height ≥ 0.5×ROI-height, sorted left-to-right; merge components whose x-ranges overlap > 60 % (handles digits split by weak segments); reject when `digit_count` configured and found count ≠ configured (→ unreadable),
   e. decimal point detection: small components (area < 20 % of median digit area) in the lower band (bottom 25 % of digit height) between digits, unless `decimal_places` fixed in config,
   f. minus sign: single horizontal bar component (aspect > 2, centered vertically) leftmost, only when `allow_negative`,
   g. per-digit decode: sample the 7 canonical segment zones (relative geometry: 3 horizontal at top/mid/bottom, 4 vertical) — a segment is ON when ≥ 40 % of its zone pixels are foreground; map the 7-bit pattern via the standard table {0,1,…,9}; also accept the common "6/9 variant without tail" patterns; unknown pattern → digit confidence 0,
   h. assemble text → apply `decimal_places` or detected point → parse float → multiply `value_scale`.
2. Confidence: mean over digits of per-segment margin (distance of zone fill-ratio from the 40 % boundary, normalized), times 1.0 when pattern known / 0 when any digit unknown. Reading with confidence < `min_confidence` returns `{"number": null, "text": ""}` shaped value (still §6.2-valid) and low confidence — pipeline handles availability.
3. `raw` debug payload: `{digit_boxes: [[x,y,w,h]…], patterns: ["1110111",…], text_prescale, applied_angle}` + base64 binarized image only when `ctx` requests debug (bool flag on `ReadContext`; default off to keep readings small).
4. Latency budget < 150 ms @ 640×480 ROI on Pi 4 (non-gating perf log test as in issue 12).
5. Determinism: identical input → identical output.

## Acceptance Criteria
- [ ] Synthetic corpus: ≥ 95 % per-frame exact-match accuracy across the generated matrix (digits 0–9, lengths 1–4, skew {0°, ±8°}, noise σ ∈ {0, 8}, incl. decimal points and minus).
- [ ] Glare subset: reader returns low-confidence/unreadable rather than a wrong confident value in ≥ 90 % of glare cases (wrong-and-confident is the failure mode that must not happen).
- [ ] `digit_count` mismatch and unknown patterns yield unreadable, never a partial guess.
- [ ] `value_scale=0.1` and fixed `decimal_places=1` behave per config on integer displays.
- [ ] Reading shape valid per §6.2; mypy strict; perf log emitted.

## Validation
`pytest tests/unit/sensing/test_sevenseg_reader.py` incl. an accuracy-report test that prints a per-category table (used to track K1). Any real-photo failure found later gets added to the corpus before fixing.

## Dependencies
10, 11.

## Non-goals
No general OCR (fonts/LCD matrix text), no ML model, no multi-line displays, no auto-ROI discovery. One display per sensor.

## Design References
DESIGN §6.2/§6.3 (sevenseg), §10.3, §16 K1; research/prior-art.md (ssocr, AI-on-the-edge-device).

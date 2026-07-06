# Implement the Web UI ROI editor and sensor configuration page

## Summary
Implement the sensor create/edit surface: draw and adjust a ROI rectangle on a live camera snapshot (custom canvas/SVG, no heavy deps), per-reader-type config forms, calibration capture buttons, and a live test-read panel with debug images — the make-or-break onboarding UX.

## Context
Defining a sensor = pointing at pixels. This page turns DESIGN §6.1/§6.3 sensor rows into a visual workflow over issue 17's endpoints (`preview`, `test-read`, `calibrate`).

## Scope
- `web/src/pages/sensors/`: `SensorEditorPage` (route `/sensors/new?camera=<id>` and `/sensors/:id`), `RoiCanvas` component, `ReaderConfigForm` (led/sevenseg/change variants), `TestReadPanel`, `CalibrationPanel`; entry points: "Add sensor" from camera card (27) and dashboard.

## Detailed Requirements
1. **RoiCanvas**: renders the camera snapshot (refresh button, `fresh=true`); pointer-driven rectangle draw (mousedown-drag-up) and edit (move body, resize via 8 handles); keyboard nudge (arrows = 1 px, shift = 10 px); zoom 1×/2×/4× centered on ROI for tight displays; coordinates shown live in *image pixels* (the API contract — canvas scales, values don't); min size 4×4; clamped to frame bounds; implemented with plain SVG/pointer events (no fabric/konva — bundle budget, issue 25-3).
2. Reader-type selector (led/sevenseg/change) switches `ReaderConfigForm`, each rendering exactly the DESIGN §6.3 fields with defaults, inline validation mirroring issue-11 models, and helper text per field (e.g., sevenseg `invert`: "dark digits on light background → on").
3. Stabilizer section (collapsed "Advanced"): §6.4 fields with defaults and plain-language hints ("report a change only after K of N frames agree").
4. **CalibrationPanel**: shows required calibration labels for the chosen reader/mode (from `missing_calibration` in API responses); per label: capture button (`POST …/calibrate`), captured-at timestamp, and re-capture. v1 shows capture success + timestamp only — no thumbnail (avoids an extra endpoint); stale-calibration warning when ROI changed after capture (compare `updated_at` vs calibration `created_at`).
5. **TestReadPanel**: "Test read" button → `POST …/test-read?debug=true`; renders value JSON prettified, confidence meter, per-stage debug images (base64) in a horizontal strip; errors render reader `raw.error` strings with guidance (`missing_calibration:baseline_off` → points at CalibrationPanel).
6. Create flow ordering: pick camera (pre-filled from query) → draw ROI → choose reader → save → calibrate → test-read; the page nudges through incomplete steps (disabled-with-reason buttons, e.g., test-read disabled until saved).
7. HA metadata fields (`unit`, `ha_device_class`) with a short datalist of common device classes (free text allowed).
8. Edit mode: ROI changes prompt "recalibrate recommended" when calibration exists; `warnings` from API (e.g., `roi_unverified`) surfaced as dismissible notes.
9. Delete sensor with confirm (history cascade warning), navigating back to the camera page.

## Acceptance Criteria
- [ ] vitest (jsdom + pointer-event simulation): draw produces expected image-pixel rect at 1× and 2× zoom; resize handles and clamping correct; keyboard nudge steps exact.
- [ ] Reader forms round-trip the §6.3 example configs byte-equal (serialize test).
- [ ] Full manual flow recorded in PR (replay camera with a 7-seg fixture image: draw ROI → save → test-read returns the number → screenshots of debug strip).
- [ ] Missing-calibration path: led brightness sensor prompts for `baseline_off`, capture clears the prompt, test-read then succeeds (manual + mocked vitest).
- [ ] Stale-calibration warning fires after ROI move (mocked timestamps).
- [ ] Bundle budget still met (issue 25-3 CI check).

## Validation
CI vitest suites + the recorded manual E2E flow in the PR description.

## Dependencies
26, 17, 15 (test-read), 11 (config semantics).

## Non-goals
No polygon/rotated ROIs (rect only, v1), no multi-ROI-per-sensor, no auto-ROI suggestion (v2 idea), no analog-gauge calibration UI (v2).

## Design References
DESIGN §11.1, §6.3–6.4, §7.2; issue 17-7/10/11 endpoint semantics.

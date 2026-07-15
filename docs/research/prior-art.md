# Prior art and positioning research

Status: Informative (verified via web search on 2026-07-06 where noted; re-verify specifics at implementation time)
Feeds: DESIGN §1.2, ADR-001, ADR-002, reader designs (issues 12–14)

## Landscape

| Project | What it is | Relation to iotify |
|---|---|---|
| [AI-on-the-edge-device](https://github.com/jomjol/AI-on-the-edge-device) (jomjol) — active, verified 2026-07-06; [docs](https://jomjol.github.io/AI-on-the-edge-device-docs/) | ESP32-CAM firmware that digitizes one analog/digital utility meter per device: on-device ROI extraction + small CNN, publishes via MQTT, HA-friendly | Strongest prior art for "camera reads a meter". Differences: one dedicated ESP32 per meter vs iotify's hub + many commodity cameras; meters only vs arbitrary lamps/displays/scenes; sensing-only vs iotify's verified control loop. Its ROI + per-digit pipeline and plausibility checks validate our reader approach. |
| ssocr (seven-segment OCR CLI, long-established) | Classical-CV recognizer for 7-seg displays (thresholding + segment sampling) | Validates that `sevenseg` is tractable without ML (issue 13 mirrors its segment-zone sampling idea). Re-check license before any code reuse; v1 plans a clean-room implementation. |
| Frigate | Local NVR with real-time object detection for IP cameras, deep HA integration | Adjacent but different job: recording + object/person detection. iotify deliberately is **not** an NVR (no recording); positioning line in DESIGN §1.2. Its local-first posture and HA-discovery ergonomics are the bar to meet. |
| ESPHome | Firmware framework incl. IR transmitters | The designated v2 path for a DIY IR blaster (ADR-002); v1 reaches actuators through HA integrations instead. |
| Home Assistant + Nature Remo / SwitchBot / Broadlink integrations | Smart-remote hubs exposed as HA `remote`/`climate` entities | The v1 actuation substrate (ADR-002). iotify calls HA services; device/protocol support is HA's problem, not ours. |
| Generic "camera OCR to HA" community recipes (e.g., HA image-processing + Tesseract glue) | Ad-hoc automations | Evidence of demand; no productized ROI/calibration/stabilization/verification layer — that gap is iotify's product. |

## Design takeaways

1. **Hub-of-many-cameras is the open niche.** Meter-per-ESP32 (AI-on-the-edge-device) and NVR (Frigate) bracket the space; a lightweight multi-camera *sensor/actuator* hub between them is unserved.
2. **Classical CV first is proven** for 7-seg and lamp states (ssocr, early AI-on-the-edge pipelines); ship classical readers in v1, keep a tiny-CNN fallback as the K1 contingency.
3. **Stabilization is where naive projects die** — flickering values and glare produce flapping sensors; a first-class debounce/hysteresis layer (issue 15) is a differentiator, not plumbing.
4. **HA MQTT Discovery is the adoption lever** — Frigate/AI-on-the-edge devices appear in HA "by magic"; iotify must match that (issue 21).
5. **Closed-loop verification has no direct prior art** in this niche — camera-verified IR control is the headline feature; design it as a visible product surface (progress UI, result events), not an internal detail.

## Sources

- [jomjol/AI-on-the-edge-device](https://github.com/jomjol/AI-on-the-edge-device)
- [AI on the Edge Device docs](https://jomjol.github.io/AI-on-the-edge-device-docs/)
- Frigate, ssocr, ESPHome, HA integration facts: from prior knowledge (stable, multi-year projects); re-verify current APIs/licenses at implementation time as flagged above.

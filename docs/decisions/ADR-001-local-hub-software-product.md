# ADR-001: v1 is a local-hub software product with local-only inference

Status: Accepted (2026-07-06)
Deciders: Saber5656 (product owner), design agent

## Context

The one-line concept ("camera-based retrofit IoT kit, no wiring") admits several product forms: dedicated hardware kit with custom firmware, a mobile-app-based product, or a self-hosted hub that reuses commodity cameras. The owner additionally requires controlling appliances from a Mac. Inference location (local vs cloud) determines the privacy posture, threat model, and OSS credibility of a product that points cameras at the inside of a home.

## Decision

1. v1 ships as **self-hosted hub software** (Python) running on **macOS and Linux** (pip + Docker), with no custom hardware. Cameras are commodity: RTSP, USB, MJPEG/snapshot HTTP (ESP32-CAM class), plus a file-replay source for tests/demos.
2. **All image processing is local-only.** No frame, crop, or derived image ever leaves the LAN. The hub makes outbound connections only to user-configured cameras, the MQTT broker, and Home Assistant.
3. macOS is a first-class hub target for trial use; an always-on Linux box (Raspberry Pi) is the reference deployment for continuous monitoring.

## Options considered

| Option | Verdict | Reason |
|---|---|---|
| A. Local hub software (chosen) | ✅ | Smallest v1, no hardware logistics, matches OSS self-host audience, Mac requirement satisfied via clients |
| B. Dedicated hardware kit (ESP32-CAM firmware first) | ❌ v1 | Firmware/enclosure/flashing/support explode scope; AI-on-the-edge-device already serves the single-device niche |
| C. Mobile-app product | ❌ | Wrong platform for an always-on monitor; hard for implementation agents to validate |
| Cloud inference | ❌ | Streaming home interior video to cloud contradicts the privacy posture and adds cost/accounts; revisit only as opt-in v2 for single-ROI stills |

## Consequences

- v1 quality hinges on classical CV readers working on commodity hardware (Pi 4 budget in DESIGN §10.3).
- ESP32-CAM devices are supported as dumb HTTP cameras, not as compute nodes.
- A future hardware "kit" (camera + mount + preflashed ESP32) can be layered on without changing the architecture.
- Privacy claims ("images never leave your LAN") become testable assertions (DESIGN §12.3 rule 4) rather than marketing.

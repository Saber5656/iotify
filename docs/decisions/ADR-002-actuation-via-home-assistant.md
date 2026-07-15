# ADR-002: v1 actuation is delegated to Home Assistant; iotify adds camera-verified closed loop

Status: Accepted (2026-07-06)
Deciders: Saber5656 (product owner), design agent

## Context

The owner wants to control appliances (e.g., an air conditioner normally driven by an IR remote) from a Mac. A camera cannot actuate anything; a physical command path is required. Candidates: drive existing smart remote hubs (Nature Remo, SwitchBot Hub, Broadlink…) through Home Assistant, ship our own ESP32+IR-LED firmware, or both.

## Decision

1. v1 sends commands **exclusively through the Home Assistant service-call API** (`POST /api/services/<domain>/<service>`), targeting entities provided by the user's existing smart-remote integrations. iotify has no device-specific IR code database and no firmware.
2. iotify's added value on the control path is the **verified control state machine** (DESIGN §9): dispatch → settle → watch a camera sensor for the expected effect → retry → report. IR is open-loop; iotify closes the loop.
3. A DIY ESP32 IR blaster reference (ESPHome-based) is deferred to v2 as documentation, not firmware development.

## Options considered

| Option | Verdict | Reason |
|---|---|---|
| A. HA-delegated actuation (chosen) | ✅ | Zero hardware scope, instantly inherits hundreds of integrations, matches "MQTT + HA" integration decision |
| B. Own IR blaster firmware in v1 | ❌ | IR code learning, per-appliance protocol quirks, flashing UX — a product in itself; ESPHome already does it |
| C. Both in v1 | ❌ | +10–15 issues and a hardware validation matrix for little unique value |
| Direct vendor cloud APIs (Nature Remo cloud etc.) | ❌ | Adds cloud dependency + credential sprawl; HA already abstracts them locally |

## Consequences

- v1 control requires a working Home Assistant with at least one remote/climate integration; this is an explicit prerequisite in docs.
- iotify needs only two HA permissions: read states, call services — enabling the "dedicated HA user" least-privilege guidance (DESIGN §12.2 T5).
- If HA is unreachable, sensing continues unaffected; control degrades gracefully (`ha_unreachable`).
- The verification engine is designed against sensor expectations, not HA state, so it also verifies devices HA merely *hopes* it controlled.

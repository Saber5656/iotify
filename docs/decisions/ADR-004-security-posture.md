# ADR-004: Security posture and secure defaults

Status: Accepted (2026-07-06)
Deciders: Saber5656 (product owner: local-only inference), design agent (defaults)

## Context

iotify points cameras at the inside of homes and holds a Home Assistant token that can drive the whole house. It is intended to be released as OSS. Security must be designed in, not patched on; defaults must protect the least-attentive installer.

## Decision

1. **Local-only**: no cloud endpoints, no telemetry, no auto-update phone-home. Outbound connections are limited to user-configured cameras, MQTT broker, and Home Assistant; a test enforces the egress inventory (DESIGN §12.3-4).
2. **Authenticated by default, no off switch**: every API/WS route (except `GET /healthz` liveness and static assets) requires the operator Bearer token; token is stored **hashed** (sha256) in `secrets.yaml`; WS uses single-use 60 s tickets.
3. **Conservative network defaults**: bind `127.0.0.1`; non-loopback bind is an explicit config change and logs a prominent warning; no UPnP, no mDNS advertisement in v1; TLS via reverse-proxy guide rather than half-baked built-in TLS.
4. **Secrets segregation**: operator secrets in `secrets.yaml` (mode `0600` enforced at startup, hub refuses to run otherwise); camera credentials in SQLite (`0600` file in `0700` dir; at-rest encryption documented as v1 limitation); global log-redaction filter; APIs never echo secrets (camera password write-only).
5. **Contained failure domains**: per-camera decode errors quarantine that camera only; input caps (snapshot ≤ 8 MiB, timeouts everywhere); pydantic `extra="forbid"` on all external inputs.
6. **Supply chain**: lockfiles for pip/npm/SwiftPM; dependabot; CodeQL (python, javascript); `pip-audit`/`npm audit` scheduled; GitHub Actions pinned by commit SHA with least-privilege `permissions:`; `SECURITY.md` with private vulnerability reporting.
7. **Privacy defaults**: no video recording ever; snapshots only for calibration + change events; retention 7 days (snapshots) / 90 days (readings); privacy guide covers camera placement and household consent.

## Options considered (deltas only)

- **mTLS / built-in HTTPS in v1**: rejected — cert UX on LAN is a tarpit; reverse proxy (Caddy/Traefik) guide achieves it better.
- **OS keyring for secrets**: rejected for v1 — headless Linux keyring support is unreliable; file + perms is auditable and scriptable.
- **Unauthenticated read-only endpoints for dashboards**: rejected — behavioral data (when you do laundry) is sensitive; T9.
- **JWT/session auth**: rejected — single-operator product; one strong token + rotation is simpler and safer to implement mechanically.

## Consequences

- Some UX friction is accepted (token entry on each new client; localhost default requires explicit LAN opt-in).
- Security acceptance criteria are embedded per issue (16, 20, 22, 36, 37 and §12.3 rules apply to all) so implementation agents cannot skip them.
- v2 candidates: sandboxed decoding (T3), DB at-rest encryption (T4), signed releases/SBOM.

# Security hardening pass: secrets audit, permissions enforcement, and server hardening verification

## Summary
A dedicated security pass over everything built in waves 0–7: verify and close gaps against the DESIGN §12 threat table and ADR-004 — secrets never leak, permissions enforced everywhere, egress inventory tested, headers/rate-limits verified, plus the SECURITY.md and hardening guide.

## Context
Individual issues carry their own security criteria; this issue is the adversarial sweep that assumes some slipped. It is intentionally scheduled after the surfaces exist (API, MQTT, HA, UI, CLI, menu bar) and before packaging/release.

## Scope
- Audit + fixes across `src/iotify/**`, `web/src/**`, `macos/**` (fix-in-place for small gaps; file follow-up issues for anything structural).
- New: `SECURITY.md` (supported versions, private reporting via GitHub Security Advisories, response expectations), `docs/guides/hardening.md` (reverse-proxy TLS recipe with Caddy example, LAN-bind checklist, dedicated HA user setup, broker auth/TLS, backup guidance incl. what files are secret).
- New automated guards (tests that keep it fixed):
  1. **Secret-leak suite**: boot full stack (hub + Mosquitto + stub HA) with canary secrets (`password=CANARY_PW_9f`, HA token, MQTT password, camera password, API token); drive traffic (CRUD, snapshots, MQTT publishes, HA calls, failed auth, error paths); assert canaries absent from: all logs (capture root handler), all API response bodies, MQTT payloads (subscriber capture), problem+json details, `system/info`.
  2. **Egress inventory test** (DESIGN §12.3-4): monkeypatch socket/httpx/aiomqtt connect layers; run the stack through a scripted scenario; assert the set of remote endpoints ⊆ {configured cameras, broker, HA base URL}.
  3. **Permissions test**: after first boot, assert modes — config dir 0700, data dir 0700, secrets.yaml 0600, DB 0600, snapshots dir 0700; startup refusal on loosened secrets.yaml re-verified end-to-end.
  4. **Headers/limits test**: security headers on every route class (API, static, healthz), auth rate-limit behavior, WS ticket single-use, snapshot size cap (8 MiB camera), `test-read` debug response cap (4 MiB).
  5. **Dependency scripts**: `make audit` = `uv run pip-audit` + `npm audit --audit-level=high` (informational here; CI gating in 37).

## Detailed Requirements
1. Walk the §12.2 threat table T1–T9 row by row; for each, record in the PR description: mitigations verified (test name/evidence) or gap found → fixed here / follow-up issue filed. This traceability table is the core deliverable.
2. Grep-based repo checks codified in a test: no `print(` of secret-bearing structures, no `logging` f-strings interpolating `password|token` fields outside redaction tests, no `verify=False`/`ssl._create_unverified` anywhere, no `subprocess` with `shell=True`.
3. Web UI: confirm CSP final form (25-1) blocks inline script injection via a vitest DOM attempt; confirm token absent from URLs and error toasts.
4. Menu bar: confirm token only in Keychain (33 test exists — re-run as part of suite matrix), URLSession no cache of authorized responses (`URLCache` disabled for the client).
5. CLI: cli.toml permission warning verified; `--token` flag documented as visible in `ps` — recommend env/file in help text (add if missing).
6. `docs/guides/hardening.md` must be executable advice: copy-paste Caddyfile, HA user creation steps, mosquitto.conf auth+TLS minimal example (referencing test certs script from issue 20 as the pattern).

## Acceptance Criteria
- [ ] Threat-table traceability recorded T1–T9 with evidence links (tests or doc sections); zero unfixed high-risk gaps.
- [ ] Secret-leak, egress, permissions, headers/limits suites green in CI (integration marker).
- [ ] Grep-guard test green.
- [ ] SECURITY.md present with private reporting instructions; hardening guide passes a fresh-eyes follow-through (execute it verbatim on a scratch VM/container, note in PR).
- [ ] Any structural gap has a filed follow-up issue referenced in the PR.

## Validation
New `tests/security/` suite in CI; manual guide walk-through evidence in PR.

## Dependencies
16, 17, 19, 20, 22, 25, 26, 31, 33 (surfaces must exist to be audited).

## Non-goals
No new features; no sandboxed decoding or DB encryption (v2 candidates per ADR-004); no penetration test (external, post-v1).

## Design References
DESIGN §12 (entire), ADR-004; issue-level security criteria it re-verifies.

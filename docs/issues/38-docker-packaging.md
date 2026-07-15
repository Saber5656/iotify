# Implement Docker packaging (multi-arch image + compose example)

## Summary
Build the official container: multi-stage Dockerfile (web build → wheel → slim runtime with OpenCV/ffmpeg), linux/amd64 + linux/arm64, non-root, healthcheck, `/config`+`/data` volumes, plus a compose example with Mosquitto — the reference always-on deployment (DESIGN §2).

## Context
Docker is how the hub lands on a Pi/NAS next to Home Assistant. The image must respect the security posture (non-root, no secrets baked, localhost-vs-LAN bind made explicit).

## Scope
- `Dockerfile` (repo root), `.dockerignore`, `compose.example.yaml`, `docs/guides/docker.md`; CI job building (not pushing) both arches on PRs touching build inputs; GHCR push wiring prepared but activated in the release workflow (39).

## Detailed Requirements
1. Stages: (a) `node:22-slim` → `npm ci && vite build` for `web/`; (b) `python:3.12-slim` + uv → build wheel with embedded static (reuses issue 39's hatch build hook — coordinate: the hook lands here if 39 hasn't merged, shared file `hatch_build.py`); (c) runtime `python:3.12-slim` + apt `ffmpeg` + `libgl1 libglib2.0-0` (opencv-headless runtime needs), `pip install` the wheel, `useradd -r -u 10001 iotify`, `USER iotify`.
2. Env defaults inside the image: `IOTIFY_CONFIG_DIR=/config`, `IOTIFY_DATA_DIR=/data`, `IOTIFY_SERVER__HOST=0.0.0.0` (container-internal; the compose example maps `127.0.0.1:8799:8799` by default with a commented LAN variant — the ADR-004-3 warning still logs and the docs explain it).
3. `VOLUME /config /data`; entrypoint `iotify serve`; `HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8799/healthz')"` interval 30 s start-period 20 s.
4. First-run token UX in containers: banner goes to container logs — `docs/guides/docker.md` leads with `docker compose logs iotify | grep -A2 token`.
5. `compose.example.yaml`: `iotify` + `eclipse-mosquitto:2` (with a minimal auth-enabled mosquitto.conf example mounted, password file creation steps in the guide — no anonymous broker in the example, matching T2), named volumes, `restart: unless-stopped`; optional commented `homeassistant` service block.
6. Image size budget ≤ 900 MB uncompressed (opencv+ffmpeg dominate; record actual in PR); build uses BuildKit cache mounts for apt/pip/npm.
7. CI: `docker buildx build --platform linux/amd64,linux/arm64` (build-only, no push) on PRs touching `Dockerfile`, `web/**`, `pyproject.toml`, `src/**`; smoke step: run amd64 image, wait healthy, `curl /healthz`, assert token banner appeared in logs, stop.
8. `.dockerignore`: everything except build inputs (explicit allowlist style).

## Acceptance Criteria
- [ ] `docker compose -f compose.example.yaml up` on amd64: hub healthy, token in logs, Web UI reachable on 127.0.0.1:8799, MQTT connects to the bundled Mosquitto after following the guide's password steps.
- [ ] arm64 image runs on a Raspberry Pi 4/5 (or QEMU if no hardware): boots healthy with a replay camera; note platform + timing in PR (K6 evidence).
- [ ] Container processes run as uid 10001 (asserted in CI smoke via `docker exec id`).
- [ ] Volumes: recreate container → config/data/token survive.
- [ ] CI build+smoke green; image size recorded and ≤ budget.
- [ ] No secrets in image layers (`docker history` check scripted in CI smoke).

## Validation
CI buildx + smoke job; manual Pi (or QEMU) run for arm64 recorded in PR; compose walk-through executed verbatim from the guide.

## Dependencies
16, 25 (web build), 01; coordinates with 39 (shared build hook).

## Non-goals
No GHCR publish (39), no HA Add-on (v2), no rootless-docker docs beyond a note, no Kubernetes manifests.

## Design References
DESIGN §2, §5.1, §15 wave 8; ADR-004-3/6; DESIGN §16 K6.

# Implement PyPI packaging with embedded Web UI and the tag-driven release workflow

## Summary
Make `pip install iotify` real: hatch build hook embedding `web/dist` into the wheel, version single-sourcing, CHANGELOG discipline, and a tag-driven GitHub Actions release workflow (build → test → publish wheel/sdist to PyPI via trusted publishing or gated token, push GHCR multi-arch image, create GitHub Release).

## Context
Release engineering closes v1 (DESIGN §15 wave 8). Human-owned secrets policy applies: the maintainer provisions PyPI trusted-publisher/registry credentials; workflows must degrade gracefully when absent (publish steps skip with a clear notice), because merge ≠ release.

## Scope
- `hatch_build.py` build hook: on wheel build, require `web/dist` present (built via `make web-build`) and copy into `iotify/server/static/`; fail with actionable message otherwise; sdist includes `web/` sources but not `node_modules`.
- Version single-source: `src/iotify/__init__.py.__version__` read by hatch (`[tool.hatch.version] path`); `iotify version` and `/system/info` already consume it.
- `CHANGELOG.md` (Keep-a-Changelog format, `Unreleased` section seeded with v1 waves).
- `.github/workflows/release.yml`: trigger `push: tags: v*`; jobs: (1) full test matrix reuse (call `ci.yml` via the `workflow_call` trigger added in issue 05; if issue 05 landed without that trigger, update `ci.yml` in this issue before adding `release.yml`), (2) build wheel+sdist (with fresh web build) + `twine check` + install-smoke (`pip install dist/*.whl && iotify version` on macOS+Linux), (3) publish PyPI — prefer **trusted publishing** (OIDC, no long-lived secret) with environment `release` requiring manual approval; skip-with-notice when the environment/publisher isn't configured, (4) buildx push GHCR `ghcr.io/saber5656/iotify:{version,latest}` (reuses issue 38 Dockerfile; `packages: write` permission scoped to this job), (5) `gh release create` with generated notes + CHANGELOG excerpt + artifacts.
- `docs/guides/release.md`: cut-a-release runbook (version bump PR → tag → approve environment → post-release verify), rollback notes (yank policy), and the maintainer-side PyPI trusted-publisher setup steps (human task).

## Detailed Requirements
1. Wheel must be functional standalone: `pip install` in a clean venv on macOS arm64 + Linux amd64 serves the embedded UI (CI install-smoke asserts `/` returns the SPA shell).
2. `pipx install iotify` path documented and smoke-tested once manually (PR evidence).
3. Tag/version guard: workflow fails fast if tag != `v${__version__}`.
4. Release workflow permissions: default `contents: read`; per-job elevation only (`id-token: write` for PyPI OIDC, `packages: write` for GHCR, `contents: write` for the release job); all actions SHA-pinned.
5. GHCR image tags immutable per version + moving `latest`; provenance/attestation flags on buildx if available without extra infra (else note as v2 with SBOM).
6. No publish on test failure anywhere upstream (job `needs` chain); dry-run mode: `workflow_dispatch` input `dry_run=true` runs everything but publish steps.
7. First release target `v0.1.0` — the runbook's example uses it.

## Acceptance Criteria
- [ ] `make web-build && uv build` produces a wheel whose installed package serves the UI; sdist rebuilds without node when `IOTIFY_SKIP_WEB=1` documented escape hatch is used (dev convenience, refuses on release workflow).
- [ ] `workflow_dispatch dry_run=true` executes green end-to-end with publish steps skipped-with-notice (evidence link).
- [ ] Tag/version mismatch fails fast (scratch-tag test on a fork/branch, evidence).
- [ ] Install-smoke green on both OS cells.
- [ ] Runbook executed once in dry-run form by the maintainer; PyPI trusted-publisher setup steps confirmed accurate against current PyPI UI (human step, checkbox in PR).
- [ ] CHANGELOG seeded; release notes template renders.

## Validation
Dry-run workflow evidence + install-smoke CI + manual runbook walk-through.

## Dependencies
01, 25, 38 (Dockerfile), 05/37 (CI reuse + gates).

## Non-goals
No actual `v0.1.0` publication in this issue (separate human-approved act), no Homebrew formula (v2), no signed artifacts/SBOM (v2 follow-up noted in release guide).

## Design References
DESIGN §15, ADR-003 (packaging), ADR-004-6; operator secret policy (§5.3).

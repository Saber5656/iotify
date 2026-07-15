# Set up CI with GitHub Actions (lint, typecheck, tests on Linux and macOS)

## Summary
Add the core CI workflow running ruff, mypy, and pytest on a Linux + macOS matrix with Python 3.11–3.13, plus PR hygiene defaults (concurrency cancellation, least-privilege permissions, SHA-pinned actions).

## Context
CI must exist before feature waves so every subsequent issue lands gated (DESIGN §14). Supply-chain workflows (CodeQL, dependabot, audits) are deliberately separate (issue 37); web/Swift jobs are added by issues 25/33.

## Scope
- `.github/workflows/ci.yml` — jobs:
  - `python` matrix `{os: [ubuntu-latest, macos-14], python: ['3.11','3.12','3.13']}`: `uv sync` → `make lint` → `make typecheck` → `pytest --cov=iotify --cov-report=xml` (coverage uploaded as artifact).
  - `integration` (ubuntu only, placeholder): runs `pytest tests/integration -m "not e2e"` with a Mosquitto **service container** (`eclipse-mosquitto:2`) wired but tolerated-empty until issue 20 adds tests.
- Workflow-level `permissions: contents: read`; `concurrency: {group: ci-${{ github.ref }}, cancel-in-progress: true}`.

## Detailed Requirements
1. Every third-party action pinned to a full commit SHA with a version comment (ADR-004-6).
2. Trigger on `pull_request`, `push` to `main`, and `workflow_call` so the release workflow (issue 39) can reuse the same test matrix before publishing.
3. Cache uv (`~/.cache/uv`) keyed on `uv.lock` hash + python version.
4. Mosquitto service container config: anonymous access enabled for CI only via a checked-in `tests/integration/mosquitto-ci.conf` mounted into the service (documented as CI-only in a header comment).
5. Total `python` job time budget ≤ 10 min per matrix cell at current repo size; fail the build on any warning from ruff.
6. Coverage threshold: informational only in this issue (no gate yet); print total to job summary.
7. A `docs-only` filter: workflows skip the heavy matrix when the diff touches only `docs/**` (use `paths-ignore`).

## Acceptance Criteria
- [ ] CI green on a PR containing this workflow + wave-0 code.
- [ ] A deliberate lint error in a scratch branch fails the `python` job (verified once, then reverted).
- [ ] macOS and Linux cells both run all unit tests.
- [ ] All actions SHA-pinned; workflow permissions are read-only.
- [ ] Docs-only PRs skip the matrix.
- [ ] `ci.yml` exposes `on: workflow_call` and can be invoked from a scratch caller workflow without changing job semantics.

## Validation
Open a draft PR with an intentional ruff violation → red; fix → green. Confirm Mosquitto service boots (job log) even with zero integration tests.

## Dependencies
01 (Makefile/tooling). 02–04 merge before or with this — matrix must run their tests.

## Non-goals
No CodeQL/dependabot/audit (issue 37), no web/Swift jobs (25/33), no release workflow (39), no coverage gate (revisit in 37).

## Design References
DESIGN §14 (gates), ADR-004-6 (workflow hardening).

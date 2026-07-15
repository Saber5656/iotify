# Set up supply-chain security automation (Dependabot, CodeQL, audit gates, coverage gate)

## Summary
Add the standing supply-chain defenses from ADR-004-6: Dependabot for all ecosystems, CodeQL for Python/JavaScript, scheduled + PR-gating dependency audits, and turn on the deferred coverage gate.

## Context
Issue 05 built functional CI; issue 36 audited the code. This issue makes the *pipeline* defend itself continuously — required before inviting outside contributions and cutting releases (38/39).

## Scope
- `.github/dependabot.yml`: weekly update PRs for `pip` (uv/pyproject), `npm` (web/), `swift` (macos/IotifyMenuBar/), `github-actions`; grouped minor/patch updates; security updates daily.
- `.github/workflows/codeql.yml`: CodeQL analysis for `python` and `javascript-typescript` on PRs to main + weekly schedule; default query suite; SARIF to code scanning.
- `.github/workflows/audit.yml`: weekly + on-demand `pip-audit` (against `uv.lock` export) and `npm audit --audit-level=high`; failure opens/updates a pinned issue via the workflow (create-issue action, SHA-pinned) rather than failing silently on a schedule.
- PR gate additions to `ci.yml`: `pip-audit` on changed lockfile PRs; coverage gate now enforced — total ≥ 75 %, patch-diff informational.
- Repo docs: `docs/guides/dependencies.md` — dependency-addition policy (rationale line, lockfile update, license check ≥ permissive), update-PR triage playbook.

## Detailed Requirements
1. All workflows: least-privilege `permissions:` blocks (`security-events: write` only where CodeQL needs it), SHA-pinned actions, `concurrency` groups.
2. Dependabot groups: `minor-and-patch` per ecosystem to keep PR volume sane; major updates individual.
3. CodeQL build mode: none/autobuild is fine for both languages (no compiled steps); confirm Swift is **not** included (CodeQL Swift support is server-side-limited; document the decision inline and rely on audits + review for Swift deps — revisit at v1.1).
4. Audit workflow must not fail-open: scheduled run failure (tool error) also surfaces via the pinned issue.
5. Coverage gate: measured on the Linux 3.12 cell only (stability); `fail_under=75` in coverage config; document how to run locally (`make coverage`).
6. Verify Dependabot config against real repo state by triggering a manual dry run where supported (or validating schema via `dependabot-cli` if available; otherwise schema-lint the YAML in CI).

## Acceptance Criteria
- [ ] Dependabot opens grouped PRs (evidence: first weekly run or manual trigger screenshot/link in PR).
- [ ] CodeQL runs green on main with zero alerts, or triaged alerts documented.
- [ ] Audit workflow: seeded known-vulnerable dev-only pin in a scratch branch produces the pinned issue, then reverted (evidence in PR).
- [ ] CI fails when coverage < 75 % (verified once by exclusion trick in scratch branch, then reverted).
- [ ] All new workflows SHA-pinned, least-privilege (checked by review + a lint step using `zizmor` or equivalent if trivially available — optional, note decision).
- [ ] `docs/guides/dependencies.md` written.

## Validation
Workflow runs linked in the PR; scratch-branch negative tests performed and reverted with evidence.

## Dependencies
05; 25 (npm ecosystem exists), 33 (swift ecosystem exists).

## Non-goals
No SBOM/signed releases (v2 with 39 follow-up), no license-scanner automation (manual policy in v1), no branch-protection changes (repo settings are owner-managed).

## Design References
ADR-004-6, DESIGN §12.2 T7, §14.

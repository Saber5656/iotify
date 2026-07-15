# Write the v1 documentation set (README, quickstart, guides, privacy/security docs)

## Summary
Produce the user-facing documentation that turns the software into a product: a rewritten README, a 15-minute quickstart, camera/HA/appliance guides, the privacy statement, and a consolidated manual-QA checklist used as the release gate.

## Context
Docs are a v1 deliverable (DESIGN §3.1-10) and several issues seeded stubs (21, 33, 36, 38, 39). This issue unifies them, fills gaps, and fixes voice/structure. Plain Markdown in `docs/` (no site generator in v1 — ADR-003 keeps toolchains minimal; mkdocs is a v2 idea).

## Scope
- `README.md` rewrite (English, with the existing Japanese one-liner kept as a tagline translation note): what/why in 5 lines, hero flow diagram (from DESIGN §4), feature list, quickstart pointer, security/privacy posture summary, status badge row, license note.
- `docs/guides/quickstart.md`: zero → first sensor → HA discovery → first verified control in ≤ 15 min using either pip or Docker path; uses a phone/webcam as the camera; includes the replay-source "try without hardware" track.
- `docs/guides/cameras.md`: RTSP/USB/MJPEG/snapshot setup per source type incl. ESP32-CAM recipe, placement/lighting/glare advice (feeds reader accuracy), troubleshooting table from the error taxonomy.
- `docs/guides/home-assistant.md` (expand 21's stub): broker setup, discovery expectations, dedicated-user + token steps (human-performed), actuator examples for Nature Remo / SwitchBot / Broadlink entity patterns.
- `docs/guides/appliances.md`: appliance/action modeling walkthrough (AC example from DESIGN §9.1), expectation-choosing guide (§9.3 decision table), verification tuning (timeout/retries/settle).
- `docs/PRIVACY.md`: exactly what is captured/stored/kept (retention defaults), what never leaves the LAN, household-consent note (T9).
- `docs/qa/release-checklist.md`: consolidated manual QA (per-surface smoke items collected from issues 27–35 PR checklists + E2E 41), used before tagging.
- Docs index `docs/README.md` linking everything; link-check in CI (lychee or equivalent, SHA-pinned, offline-tolerant config).

## Detailed Requirements
1. Every guide executable top-to-bottom on a clean machine; each ends with "you now have / next" links.
2. Quickstart tested against the real artifacts (pip wheel or local `make` equivalents) — record timing evidence in PR (target ≤ 15 min excluding downloads).
3. Terminology locked to DESIGN glossary usage (camera / sensor / reader / appliance / action / run); no synonyms.
4. All commands copy-pasteable; placeholders in `<angle-brackets>` with a legend; no `$` prompts inside code blocks.
5. README security/privacy summary must match ADR-004 verbatim claims (local-only, authenticated, retention) — no marketing overreach.
6. Screenshots: dashboard, ROI editor, appliance run, menu bar (from issues 29/28/30/35 PR evidence, regenerated at consistent window sizes); stored under `docs/images/` ≤ 300 KB each.
7. Known limitations section (honest list: v1 non-goals from DESIGN §3.2 + K-risks worth users knowing: glare sensitivity, IR open-loop caveats even with verification, restart loses in-flight runs).

## Acceptance Criteria
- [ ] Fresh-machine quickstart executed verbatim by someone other than the author (or a clean VM run), timing recorded, zero undocumented steps.
- [ ] Link check green in CI; docs index complete; no orphan guide.
- [ ] README review: 5-line pitch + diagram render correctly on GitHub; tagline preserved.
- [ ] PRIVACY.md and README claims cross-checked against ADR-004 (reviewer checklist item).
- [ ] Release checklist dry-run performed once against the current build and stored with results.
- [ ] All screenshots present, sized, current.

## Validation
CI link-check; clean-environment quickstart run with timing evidence; reviewer checklist in PR.

## Dependencies
21, 27–35 (surfaces + stubs exist), 38, 39 (install paths documented).

## Non-goals
No docs site generator (v2), no translations beyond the tagline note (i18n scaffold ships English v1), no video tutorials.

## Design References
DESIGN §3.1-10, §11, §12; ADR-004; research takeaway 4 (adoption).

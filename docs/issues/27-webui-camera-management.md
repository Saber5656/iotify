# Implement Web UI camera management pages

## Summary
Implement the Cameras page: list with live health, add/edit forms per source type, connection test with actionable errors, live snapshot preview, and safe deletion — the UI over issue 17's camera endpoints.

## Context
Camera setup is the first onboarding step (DESIGN §11.1). Form ergonomics decide whether a non-expert gets to their first sensor; error surfaces must translate the camera error taxonomy into human guidance.

## Scope
- `web/src/pages/cameras/`: `CamerasPage` (list), `CameraForm` (create/edit modal or route), `CameraCard` components.

## Detailed Requirements
1. List: card per camera — name, id, source type, health badge (ONLINE green / DEGRADED amber / OFFLINE red / STARTING grey, live via WS `camera_status`), sensor count, last-frame age; snapshot thumbnail (auto-refresh every 10 s while visible, `?fresh=false`).
2. Create form: source-type selector drives visible fields — rtsp: url (+username/password optional); usb: device_index; mjpeg/snapshot: url (+auth); replay: path (labeled "for testing/demos"). Client-side validation mirrors §7.3 (id slug regex with inline hint, scheme-per-type); id auto-suggested from name (slugified) but editable; id immutable in edit mode (rendered read-only with tooltip).
3. Password field: write-only UX — edit form shows `has_password` as "password set — leave blank to keep, check 'clear' to remove" per issue 17-2 semantics.
4. "Test connection" button (form + card menu): calls `POST /cameras/{id}/test` (in create flow: prompts to save first — test requires a persisted camera; document in helper text); result panel maps taxonomy → guidance table: `camera_auth_failed` → "check username/password", `camera_unavailable` → "check URL/host reachable", `camera_timeout` → "camera too slow / network", decode errors → "unsupported stream format".
5. Snapshot preview in edit view: large image with `fresh=true` refresh button (spinner during the ≤ 10 s fetch; 503/504 render the taxonomy guidance, not raw errors).
6. Delete: `<ConfirmDialog>` warns with the cascade consequence ("removes N sensors and their history"); success toast; list updates.
7. Poll-interval field: numeric 0.5–3600 s step 0.5 with helper text tying it to reading cadence; rotation selector 0/90/180/270 with preview hint.
8. Empty state: "Add your first camera" CTA + link to camera setup guide (docs/guides, issue 40 — link target may 404 until then; use relative doc URL).
9. All mutations optimistic-update-free (simple refetch after 2xx — correctness over flash).

## Acceptance Criteria
- [ ] Full CRUD flows work against a live hub with a replay camera (manual smoke recorded in PR: add → test → snapshot → edit interval → delete).
- [ ] vitest: form validation cases (bad id, wrong scheme per type, usb without index), password keep/clear semantics payloads, taxonomy→guidance mapping.
- [ ] Health badges update live when the backing camera goes offline (manual smoke: stop replay dir camera; badge flips ≤ 15 s).
- [ ] No password value ever rendered back into the DOM after save (vitest asserts form reset).
- [ ] Deep link `/cameras` renders standalone (router + guard intact).

## Validation
CI web job (vitest suites); manual smoke checklist in PR description with screenshots.

## Dependencies
26, 17.

## Non-goals
No sensor/ROI editing (28), no camera auto-discovery, no multi-select bulk ops.

## Design References
DESIGN §11.1, §7.2–7.3; issue 06 error taxonomy; issue 17 semantics.

# Scaffold the macOS menu bar app (SwiftUI MenuBarExtra, settings, Keychain, API client)

## Summary
Create `macos/IotifyMenuBar/`: a SwiftPM-based SwiftUI `MenuBarExtra` app (macOS 13+) with a settings window (hub URL + token stored in Keychain), a typed Swift API client for the endpoints the app needs, connection-status handling, and launch-at-login — the foundation issues 34/35 build on.

## Context
The owner explicitly chose a v1 menu bar app (ADR-003). v1 distribution is build-from-source; the scaffold must make `swift build` + `make menubar` the entire story, with CI compiling it on macOS runners.

## Scope
- `macos/IotifyMenuBar/Package.swift` (executable target `IotifyMenuBar`, swift-tools 5.9, platform `.macOS(.v13)`; test target `IotifyMenuBarTests`).
- Sources: `App.swift` (`@main` `MenuBarExtra` with placeholder menu: status line, "Open Web UI", Settings…, Quit), `Settings/SettingsView.swift` + `SettingsStore.swift`, `Keychain.swift` (Security-framework wrapper: save/load/delete generic password, service `dev.iotify.menubar`, account = hub URL host), `Api/ApiClient.swift`, `Api/Models.swift`, `Api/WsTicketClient.swift` (ticket mint only; WS stream lands in 34), `LoginItem.swift` (`SMAppService.mainApp` register/unregister).
- `Makefile` targets: `menubar-build` (`swift build -c release --package-path macos/IotifyMenuBar`), `menubar-run`; `docs/guides/menubar.md` (build/run/grant-notifications, uninstall incl. Keychain cleanup and login-item removal).
- CI: macOS job step building the package + running unit tests (added to ci.yml).

## Detailed Requirements
1. **ApiClient** (`URLSession` async/await): `systemInfo()`, `latestReadings()`, `appliances()`, `run(applianceId, action, params, verify)`, `runStatus(runId)`, `wsTicket()`; Bearer header from Keychain; JSON decoding with `Codable` models mirroring server schemas (snake_case strategy); errors as `ApiError` enum {unauthorized, unreachable, server(status, detail), decoding} parsed from problem+json.
2. **SettingsView**: hub URL text field (validated http/https URL), token secure field (never echoed after save; "token set" state like the web UI), "Test connection" button → `systemInfo()` with result inline; launch-at-login toggle; token stored **only** in Keychain (no UserDefaults, no plaintext files); URL in UserDefaults (non-secret).
3. Menu placeholder content: connection dot (green ok / red unreachable / grey unconfigured) + hub version when connected; "Open Web UI" opens `hubURL` in default browser; unconfigured state deep-links to Settings.
4. Poll `systemInfo()` every 30 s for the status dot (timer paused when menu closed is unnecessary in v1 — keep simple, note battery triviality); all requests 10 s timeout.
5. HTTP allowed: `NSAppTransportSecurity` — SwiftPM executables lack Info.plist by default; provide the bundling recipe: a minimal `Info.plist` via `-Xlinker -sectcreate` alternative is fragile → ship `make menubar-bundle` assembling a minimal `.app` bundle (Contents/MacOS binary + Info.plist template with `NSAllowsLocalNetworking`) — document that plain `swift run` works for `http://127.0.0.1` and the bundle path is for LAN hubs; template committed under `macos/IotifyMenuBar/Bundle/`.
6. Unit tests (XCTest, no network): ApiClient against `URLProtocol` mock — auth header injection, problem+json mapping, model decoding from fixture JSON (copied from server OpenAPI examples); Keychain wrapper round-trip (uses the real Keychain on CI mac runners — guard with a test-service name and cleanup).
7. Swift formatting: `swift-format` config committed; CI check step.

## Acceptance Criteria
- [ ] `make menubar-build` succeeds on a clean macOS 13+ machine with Xcode CLT only; `make menubar-run` shows the icon; Settings saves URL+token (token retrievable only via Keychain, verified by test) and "Test connection" reports hub version against a local hub.
- [ ] Launch-at-login toggle registers/unregisters (verified via `SMAppService.status`).
- [ ] `make menubar-bundle` produces a runnable `.app` reaching an `http://<LAN-IP>` hub.
- [ ] CI macOS job compiles + tests green; swift-format check passes.
- [ ] Uninstall guide steps actually remove login item + Keychain entry (manually verified, recorded in PR).

## Validation
XCTest suite in CI; manual smoke on a real Mac (screenshots: settings, status dot states) in PR.

## Dependencies
16 (API/auth), 19 (ticket endpoint shape).

## Non-goals
No sensor list/controls (34/35), no WS streaming (34), no signing/notarization/distribution (v2 — DESIGN §16 K8), no Sparkle.

## Design References
DESIGN §11.3, §7.1–7.2; ADR-003 (menu bar decision), ADR-004-4 (Keychain).

# Implement the Home Assistant actuator bridge (REST client)

## Summary
Implement `iotify.control.ha_client`: an httpx-based Home Assistant REST client (handshake, entity states, service calls) with strict timeouts, an explicit error taxonomy, and zero token leakage — the only egress path to HA (DESIGN §8.3).

## Context
ADR-002 delegates all actuation to HA service calls. This client is used by the appliance API (23) for entity pickers/validation and by the verification engine (24) for dispatch.

## Scope
- `src/iotify/control/ha_client.py`: `HaClient` — `check() -> HaInfo`, `list_entities(domain: str | None) -> list[EntityBrief]`, `get_state(entity_id) -> EntityState`, `list_services() -> dict[domain, dict[service, meta]]`, `call_service(domain, service, target_entity, data: dict) -> None`; connection-state property for `/system/info`.

## Detailed Requirements
1. Base URL from config (`home_assistant.base_url`), token from secrets (`home_assistant_token`), header `Authorization: Bearer <token>`; client built once (connection pooling), `timeout=httpx.Timeout(10.0, connect=5.0)`.
2. Endpoints used (and only these — egress inventory, DESIGN §12.3-4): `GET /api/`, `GET /api/states`, `GET /api/states/<entity_id>`, `GET /api/services`, `POST /api/services/<domain>/<service>` with body `{"entity_id": target, **data}`.
3. Error taxonomy (exceptions carry no token material): `HaDisabled` (config off), `HaUnreachable(detail)` (connect/timeout/5xx), `HaAuthFailed` (401/403), `HaServiceError(status, message)` (4xx from service call, message truncated 500 chars).
4. Retries: idempotent GETs retried ×2 with 0.5/1 s backoff on connect errors only; `call_service` **never** auto-retried (retry policy belongs to the verification state machine — DESIGN §8.3).
5. `list_entities` returns `{entity_id, friendly_name, domain, state}` filtered by domain param; result cached 30 s (UI picker churn) with explicit `refresh=True` bypass.
6. `entity_id` inputs validated `^[a-z_]+\.[a-z0-9_]+$` before URL interpolation (no path injection).
7. `check()` at startup when enabled: logs one line success (`HA reachable, version …`) or a warning; hub still boots when HA is down (sensing unaffected — ADR-002 consequence).
8. Unit tests via `httpx.MockTransport`; an optional live-HA smoke script `scripts/ha_smoke.py` (prints check + entity count; excluded from CI).

## Acceptance Criteria
- [ ] MockTransport tests: success paths for all five endpoints; 401→`HaAuthFailed`; timeout→`HaUnreachable`; 400 service call→`HaServiceError` with HA's message; GET retry fires exactly twice then surfaces.
- [ ] `call_service` on connect-error surfaces immediately without retry (asserted call count 1).
- [ ] Malformed entity_id rejected before any request.
- [ ] Token never in logs/exceptions (redaction + repr tests).
- [ ] Cache: two `list_entities` calls within 30 s hit transport once; `refresh=True` busts.
- [ ] Hub boots cleanly with HA disabled and with HA unreachable.

## Validation
`pytest tests/unit/control/test_ha_client.py`; manual `scripts/ha_smoke.py` against a real HA recorded in PR (evidence for auth + service call against a harmless entity, e.g. `light.turn_on` on a test helper).

## Dependencies
02, 03, 16 (secrets/config/lifecycle wiring).

## Non-goals
No HA WebSocket API (REST suffices for v1 scale), no entity registry caching beyond 30 s, no HA add-on.

## Design References
DESIGN §8.3, §12.2 T5, §12.3-4; ADR-002.

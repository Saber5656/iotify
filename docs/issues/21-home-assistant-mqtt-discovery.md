# Implement Home Assistant MQTT Discovery publishing

## Summary
Implement `iotify.integrations.mqtt.discovery`: retained HA discovery config payloads per sensor (DESIGN §8.2) so iotify sensors appear in Home Assistant automatically, grouped into devices per camera, with correct availability semantics.

## Context
Auto-discovery is the adoption lever (research takeaway 4). Payload correctness is a *contract with HA*: pin exact field names against the current HA MQTT Discovery documentation during implementation (DESIGN §16 K3).

## Scope
- `discovery.py`: payload builders + lifecycle publisher reacting to sensor CRUD/enable events and (re)connect.

## Detailed Requirements
1. Topic: `<prefix>/<component>/iotify_<sensor_id>/config`, retained, QoS 1; prefix from config (`homeassistant` default).
2. Component mapping (DESIGN §8.2): led → `binary_sensor` (payload maps `value_json.state == "on"`), change → `binary_sensor` (configurable `device_class`, default `motion`; `off_delay` = reader `cooldown_s`), sevenseg → `sensor` (`value_template` extracting `value_json.number`, `unit_of_measurement` from sensor.unit, `state_class: measurement`, `device_class` from sensor.ha_device_class when set).
3. Common payload fields: `name` (sensor.name), `unique_id: iotify_<sensor_id>`, `state_topic`, `availability` array (bridge status + sensor availability, `availability_mode: all`), `device` block per camera `{identifiers:["iotify_cam_<camera_id>"], name: camera.name, manufacturer:"iotify", model:"camera sensors", via_device:"iotify_hub_<hostid>"}` plus a hub device published once `{identifiers:["iotify_hub_<hostid>"], name:"iotify hub", sw_version: iotify version}`, and `origin {name:"iotify", sw_version, support_url}`.
4. Lifecycle: publish configs on MQTT connect (all enabled sensors) and on sensor create/update/enable; publish **empty retained payload** on sensor delete/disable (and camera delete → all its sensors); no discovery when `mqtt.discovery.enabled: false`.
5. Rename handling: `unique_id`/topics never change (id-based); only `name`/metadata fields change on update (republish).
6. Value templates must tolerate `number: null` (unreadable sevenseg) — template renders `unknown` (use `| default(none)` semantics; verify against HA docs during implementation).
7. Contract tests: golden JSON files per reader type under `tests/fixtures/discovery/` compared byte-stable (sorted keys); a checklist in the PR description records the HA docs version consulted (K3 evidence).
8. Manual validation guide `docs/guides/home-assistant.md` (start here; expanded in issue 40): compose snippet with HA + mosquitto, steps to see a replay-camera sensor appear in HA.

## Acceptance Criteria
- [ ] Golden payload tests for led/sevenseg/change match the documented HA discovery schema (fields above, sorted-key stable).
- [ ] Integration: with Mosquitto, creating an enabled sensor publishes retained config; a fresh test subscriber (simulating HA restart) receives config + state + availability without any hub action.
- [ ] Delete/disable clears the retained config topic (subscriber sees zero-length payload).
- [ ] Hub + camera device hierarchy present (`via_device` chain) in payloads.
- [ ] `discovery.enabled:false` publishes nothing (asserted).
- [ ] Manual HA smoke (real or containerized HA) performed once and recorded in the PR with a screenshot of the discovered device page.

## Validation
`pytest tests/unit/integrations/test_discovery_payloads.py` (golden) + `tests/integration/test_discovery_lifecycle.py` (Mosquitto). Manual HA check per requirement 8.

## Dependencies
20; 17 (CRUD events).

## Non-goals
No HA REST/actuator work (22), no discovery for appliances (iotify appliances are *driven by* HA, not exposed to it — ADR-002), no custom HA integration/add-on (v2).

## Design References
DESIGN §8.2, §16 K3; research takeaway 4.

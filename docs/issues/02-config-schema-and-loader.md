# Implement configuration schema, loader, and XDG path resolution

## Summary
Implement `iotify.config`: pydantic v2 models for `config.yaml` and `secrets.yaml`, XDG-based directory resolution with env/flag overrides, fail-fast validation, and secrets file permission enforcement.

## Context
Every subsystem consumes typed config (DESIGN §5). Entities (cameras/sensors/appliances) are *not* in YAML — they live in SQLite (issue 04); this issue covers infrastructure config only.

## Scope
- `src/iotify/config/paths.py`: `resolve_config_dir()`, `resolve_data_dir()` honoring `IOTIFY_CONFIG_DIR`/`IOTIFY_DATA_DIR`, then `XDG_CONFIG_HOME`/`XDG_DATA_HOME`, then `~/.config/iotify` / `~/.local/share/iotify`; `ensure_dirs()` creates them `0700`.
- `src/iotify/config/models.py`: `ServerConfig`, `MqttConfig` (+`MqttTlsConfig`, `DiscoveryConfig`), `HomeAssistantConfig`, `StorageConfig`, `LoggingConfig`, root `AppConfig`; separate `Secrets` model (`api_token_sha256`, `mqtt_password`, `home_assistant_token` — all optional strings).
- `src/iotify/config/loader.py`: `load_config(config_dir) -> AppConfig`, `load_secrets(config_dir) -> Secrets`, `write_secrets(...)` (atomic write, chmod 0600).

## Detailed Requirements
1. Field defaults exactly as DESIGN §5.2 (host `127.0.0.1`, port `8799`, base_topic `iotify`, discovery prefix `homeassistant`, retention 90/7 days, logging level `info`).
2. All models `model_config = ConfigDict(extra="forbid")`; unknown YAML keys must produce an error naming the offending key and file.
3. Environment overrides: `IOTIFY_<SECTION>__<KEY>` (double underscore nesting) via pydantic-settings, applied on top of YAML.
4. Missing `config.yaml` → defaults + an INFO log "created example config"; write a commented example file `config.yaml` on first run (containing defaults, no secrets).
5. `load_secrets`: if file exists with mode other than `0600` (mask `0077` bits set) → raise `SecretsPermissionError` with the exact `chmod 600 <path>` remediation string (DESIGN §5.3, ADR-004-4). Missing file → empty `Secrets`.
6. `write_secrets` writes to `secrets.yaml.tmp` then `os.replace`, setting `0600` before rename.
7. Validation extras: port 1–65535; `home_assistant.base_url` must parse as http/https URL; `mqtt.tls.ca_cert` path must exist when TLS enabled; retention days ≥ 1.
8. Custom exception hierarchy in `iotify.config`: `ConfigError` → `ConfigFileError`, `SecretsPermissionError`.

## Acceptance Criteria
- [ ] Loading an empty config dir yields defaults and writes a commented example `config.yaml`.
- [ ] Unknown key `serverx:` fails with a message containing `serverx` and the file path.
- [ ] `IOTIFY_SERVER__PORT=9000` overrides YAML value.
- [ ] `secrets.yaml` with mode `0644` raises `SecretsPermissionError` containing `chmod 600`.
- [ ] `write_secrets` result has mode `0600`; interrupted-write simulation leaves no corrupt file.
- [ ] mypy strict passes; unit tests cover every requirement above.

## Validation
`pytest tests/unit/config` (new tests, ≥ 12 cases incl. tmp-dir XDG overrides on both macOS and Linux path conventions); `make lint typecheck test`.

## Dependencies
01-repo-scaffold-python-package.

## Non-goals
No DB entities, no CLI flags plumbing (`serve` comes in issue 16), no keyring, no encryption at rest.

## Design References
DESIGN §5 (files/dirs/schemas), ADR-004 (secrets rules).

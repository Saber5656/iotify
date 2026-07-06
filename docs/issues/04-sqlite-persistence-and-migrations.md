# Implement SQLite persistence layer, migrations, and retention job

## Summary
Implement `iotify.storage`: aiosqlite connection management (WAL), sequential SQL migration runner, typed repository functions for all tables in DESIGN §6.1, and a periodic retention job for readings/snapshots.

## Context
Entities, readings, events, and calibration images all persist in one SQLite file `<data>/iotify.db` (DESIGN §6). Every later subsystem reads/writes through this layer only — no inline SQL elsewhere.

## Scope
- `src/iotify/storage/db.py`: `Database` class — `open(path)`, `close()`, `execute/fetch` helpers, single writer connection + `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`, `busy_timeout=5000`.
- `src/iotify/storage/migrations/0001_init.sql`: full schema exactly as DESIGN §6.1 (tables `cameras`, `sensors`, `readings`, `events`, `appliances`, `appliance_actions`, `calibration_images`, `schema_migrations`, all indexes and CHECK constraints).
- `src/iotify/storage/repos.py`: dataclass row models (`CameraRow`, `SensorRow`, `ReadingRow`, `EventRow`, `ApplianceRow`, `ApplianceActionRow`, `CalibrationImageRow`) + CRUD/query functions per table.
- `src/iotify/storage/retention.py`: `run_retention(db, storage_config, now_ms)` deleting readings older than `readings_retention_days`, events older than 2× that, snapshot files + `calibration_images` rows with label != `baseline_*` older than `snapshot_retention_days`; scheduled every 6 h by the app (wiring in issue 16).

## Detailed Requirements
1. Migration runner: read `schema_migrations`, apply missing `NNNN_*.sql` files in order, each inside a transaction, insert version row; refuse to start if DB has a version the code does not know (forward-compat guard).
2. DB file created with mode `0600` (open with `os.open` flags or chmod immediately after create); data dir `0700` (from issue 02 helper).
3. Repos API (minimum): `create/get/list/update/delete` for cameras, sensors, appliances (+embedded actions replace-on-update semantics); `insert_reading`, `latest_reading_per_sensor()`, `readings_range(sensor_id, from_ms, to_ms, limit, downsample_buckets)`; `insert_event`, `events_query(kind, from_ms, to_ms, limit)`; `add_calibration_image`, `list_calibration_images(sensor_id)`.
4. Downsampling: when `downsample_buckets=N` given, bucket by time and return per-bucket `{ts: bucket_start, value: last, min, max}` for numeric readers, `last` only otherwise (SQL group-by on `ts / bucket_width`).
5. ID validation (`^[a-z][a-z0-9_]{0,31}$`) enforced in repos on create; id immutability enforced on update.
6. All timestamps epoch ms UTC; `now_ms()` helper in `storage/db.py`.
7. JSON columns (`value`, `reader_config`, `stabilizer_config`, `service_data`, `payload`, `verify_expect`) are serialized/deserialized in repos, callers see dicts.
8. Deleting a sensor deletes its readings/calibration rows via FK cascade **and** its snapshot files (repo deletes files listed in `calibration_images` first).

## Acceptance Criteria
- [ ] Fresh start creates DB (mode `0600`), applies `0001`, records version 1.
- [ ] Unknown future version in `schema_migrations` aborts startup with a clear error.
- [ ] CHECK/FK constraints verified by tests (bad `source_type` rejected; cascade deletes work; ON DELETE SET NULL for `verify_sensor_id`).
- [ ] `readings_range` with `downsample_buckets=100` over 10k rows returns ≤ 100 buckets with correct min/max.
- [ ] Retention deletes exactly the expired rows/files and logs a summary line.
- [ ] Concurrent write smoke test (2 tasks × 500 inserts) passes without `database is locked`.

## Validation
`pytest tests/unit/storage` (tmp DB per test; ≥ 20 cases). Include a migration idempotency test (open twice).

## Dependencies
01, 02 (paths), 03 (logging).

## Non-goals
No ORM, no down-migrations, no at-rest encryption (ADR-004 limitation), no server wiring.

## Design References
DESIGN §6.1–6.5, §5.1, ADR-003 (SQLite choice), ADR-004-4.

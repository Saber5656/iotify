# Define the Reader plugin interface, per-type config models, and reader registry

## Summary
Implement `iotify.sensing.readers.base`: the pure-function `Reader` contract, pydantic config models for the three v1 reader types (led/sevenseg/change), config validation helpers, and the reader registry keyed by `reader_type`.

## Context
Sensors store `reader_type` + `reader_config` JSON (DESIGN §6.1/§6.3). The API layer (17) validates configs at write time and the pipeline (15) instantiates readers per sensor via this registry. Readers stay deterministic and I/O-free for golden-image testing (DESIGN §10.2).

## Scope
- `src/iotify/sensing/readers/base.py`:
  ```python
  class Reader(ABC):
      config_model: ClassVar[type[BaseModel]]
      def __init__(self, config: BaseModel): ...
      @abstractmethod
      def read(self, image: np.ndarray, ctx: ReadContext) -> Reading: ...
  ```
  `ReadContext` dataclass: `{sensor_id: str, calibration: dict[str, np.ndarray]}` — calibration images (e.g., `baseline_off`) are *loaded by the pipeline* and injected, keeping readers I/O-free. `ctx.calibration` may be empty.
- Config models `LedConfig`, `SevensegConfig`, `ChangeConfig` with fields/defaults exactly per DESIGN §6.3, `extra="forbid"`, cross-field validators: `decimal_places` and `digit_count` are independently optional, but when both are provided, `decimal_places < digit_count` must hold.
- Registry: `reader_registry: dict[str, type[Reader]]`; `validate_reader_config(reader_type, raw: dict) -> BaseModel` (raises `ReaderConfigError` with field-level details); `create_reader(reader_type, raw) -> Reader`.
- Declared calibration requirements: `Reader.required_calibration: ClassVar[set[str]]` (e.g., led-brightness mode → `{"baseline_off"}`); helper `missing_calibration(sensor, images) -> set[str]` used by pipeline/API to surface "needs calibration" instead of failing cryptically.

## Detailed Requirements
1. `read()` must not raise for merely-unreadable content — it returns a `Reading` with `confidence=0.0` and a `raw={"error": "<reason>"}`; only programmer errors raise.
2. `Reading.value` dict must match the §6.2 union for the reader type; a shared `validate_reading_shape(reader_type, value)` helper asserts this in tests and in pipeline debug mode.
3. Registry raises `ReaderConfigError` listing valid types on unknown `reader_type` (single source of truth: `sensors.reader_type` CHECK values in DESIGN §6.1 — add a cross-check test that the registry keys equal the SQL CHECK set).
4. Readers are stateless across calls (temporal logic belongs to the stabilizer, issue 15); document this contract in the module docstring.
5. This issue lands with the three config models plus a `NullReader` (returns `confidence=0` always) registered under a test-only key for pipeline tests; real readers arrive in 12–14 and register themselves here.

## Acceptance Criteria
- [ ] `validate_reader_config("led", {"mode":"brightness"})` returns a `LedConfig` with defaults; unknown field fails with field name in message.
- [ ] `validate_reader_config` for all three types round-trips the DESIGN §6.3 examples verbatim.
- [ ] Registry-keys == SQL CHECK values test passes.
- [ ] `missing_calibration` returns `{"baseline_off"}` for a brightness-mode led sensor with no calibration images.
- [ ] mypy strict; ≥ 12 unit tests.

## Validation
`pytest tests/unit/sensing/test_reader_base.py`.

## Dependencies
04 (schema check cross-test), 10 (types).

## Non-goals
No actual recognition logic (12–14), no dynamic entry-point plugin loading (explicit registry only in v1), no async readers.

## Design References
DESIGN §6.2/§6.3, §10.2, §16 K1.

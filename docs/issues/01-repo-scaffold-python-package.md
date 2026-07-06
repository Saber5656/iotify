# Scaffold the Python package, dev tooling, and repository layout

## Summary
Create the `iotify` Python package skeleton (src layout), dev tooling (uv, ruff, mypy, pytest, pre-commit), Makefile targets, license, and base repo hygiene files so every later issue lands into a working build.

## Context
The repository currently contains only `README.md` and `docs/`. All subsequent issues assume the layout in DESIGN §4.3 and the toolchain in ADR-003.

## Scope
- `pyproject.toml` (hatchling build backend, project metadata, `iotify` console script)
- `src/iotify/__init__.py` (`__version__ = "0.1.0.dev0"`), `src/iotify/__main__.py` (delegates to CLI entry point placeholder that prints version and exits 0)
- Package subdirectories from DESIGN §4.3 as empty packages with `__init__.py`: `cli`, `config`, `events`, `cameras`, `sensing`, `sensing/readers`, `storage`, `storage/migrations` (as package data dir), `integrations/mqtt`, `control`, `server`, `server/api`
- `tests/` with `unit/`, `integration/`, `e2e/`, `fixtures/images/.gitkeep` and one placeholder test asserting the package imports and version string
- Tooling config: ruff (lint+format), mypy (strict for `src/iotify`), pytest (`tests/`), coverage config
- `uv.lock` committed; `Makefile` with targets `setup`, `lint`, `typecheck`, `test`, `run`
- `.gitignore` (Python, node, macOS, `.venv`, `web/dist`, `*.db`), `.editorconfig`, `LICENSE` (Apache-2.0 — flagged for human confirmation per DESIGN §16 K9), `CONTRIBUTING.md` stub

## Detailed Requirements
1. Python floor `>=3.11` in `pyproject.toml`; classifiers for 3.11–3.13.
2. Runtime dependencies declared but minimal at this stage: `typer`, `pydantic>=2`, `pydantic-settings`, `pyyaml`. (Later issues add their own; each addition needs a rationale line in its PR per DESIGN §12.3-5.)
3. Dev dependencies: `ruff`, `mypy`, `pytest`, `pytest-asyncio`, `pytest-cov`, `pre-commit`.
4. Console script: `iotify = "iotify.cli.main:app"` — create `src/iotify/cli/main.py` with a Typer app exposing only `version` for now.
5. `make setup` = `uv sync`; `make lint` = `ruff check . && ruff format --check .`; `make typecheck` = `mypy src`; `make test` = `pytest`.
6. Pre-commit hooks: ruff check+format, end-of-file-fixer, check-added-large-files (max 1 MB, images in `tests/fixtures` exempted via args).
7. mypy: `strict = true`, per-module relaxation allowed only for `tests.*`.

## Acceptance Criteria
- [ ] `uv sync && make lint typecheck test` passes on a clean checkout (macOS and Linux).
- [ ] `uv run iotify version` prints `0.1.0.dev0`.
- [ ] `python -m iotify` behaves identically to the console script.
- [ ] All directories from DESIGN §4.3 exist as importable packages.
- [ ] LICENSE (Apache-2.0), `.gitignore`, `.editorconfig`, `CONTRIBUTING.md` present.
- [ ] No file in the repo exceeds pre-commit size limits; `uv.lock` committed.

## Validation
Run `make setup lint typecheck test` and `uv run iotify version` locally; both must succeed from a pristine clone in a temp directory.

## Dependencies
None (first issue).

## Non-goals
No FastAPI app, no config loading, no CI workflow (issue 05), no web/ or macos/ scaffolds (issues 25, 33).

## Design References
DESIGN §4.3 (layout), ADR-003 (stack, license), DESIGN §12.3-5 (dependency policy).

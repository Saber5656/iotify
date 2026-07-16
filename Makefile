.PHONY: setup lint typecheck test run

PATH := $(CURDIR)/.venv/bin:$(PATH)
export PATH

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src

test:
	uv run pytest

run:
	uv run iotify version

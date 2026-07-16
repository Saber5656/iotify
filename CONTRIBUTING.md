# Contributing

This repository is in early v1 implementation.

## Development setup

Install `uv`, then run:

```bash
make setup
make lint typecheck test
```

## Scope discipline

Implementation work is tracked by the issue files in `docs/issues/`.
Keep pull requests scoped to one issue unless the dependency plan explicitly
calls for a combined change.

## Dependency policy

Every new runtime dependency must include a short rationale in the pull request,
following DESIGN §12.3-5.

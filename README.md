# lapwise

FastAPI wrapper for the [OpenF1](https://openf1.org) public API.

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn lapwise.main:app --reload
```

## Test

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check
uv run ruff format --check
```

## Type check

```bash
uv run mypy src
```

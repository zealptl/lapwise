## Why

We need a FastAPI backend that wraps the public OpenF1 API so we can: (1) own the contract our clients depend on, (2) introduce a service layer where future derived endpoints (analytics, transformations) can be composed without leaking HTTP details, and (3) publish detailed OpenAPI documentation that OpenF1 itself does not provide. Greenfield repo — nothing exists yet.

## What Changes

- Introduce a Python 3.12 FastAPI project managed with `uv`, with a layered architecture: routes → services → OpenF1 client.
- Expose 13 wrapper endpoints under `/v1/*` whose paths mirror OpenF1 exactly (`/v1/drivers`, `/v1/laps`, `/v1/meetings`, `/v1/overtakes`, `/v1/pit`, `/v1/position`, `/v1/sessions`, `/v1/session_result`, `/v1/starting_grid`, `/v1/stints`, `/v1/weather`, `/v1/championship_drivers`, `/v1/championship_teams`).
- Reserve `/v1/analysis/*` as the future home of derived endpoints (no endpoints in this change).
- Adopt **hybrid filter syntax**: equality and repeated-key `in` filters mirror OpenF1; comparisons use suffixes `_lt` / `_lte` / `_gt` / `_gte`. Translator converts these back to OpenF1's native operator syntax.
- All endpoints return typed Pydantic models that **mirror OpenF1's raw shapes** (Union types where OpenF1 itself is messy, e.g. `gap_to_leader: float | str | None`).
- Upstream errors mapped: OpenF1 5xx → `502`, timeout → `504`, OpenF1 4xx forwarded; structured error envelope in all error responses.
- Rich OpenAPI documentation per endpoint: summary, multi-paragraph description, per-parameter descriptions, response model with field descriptions, success and error response examples, tags (`OpenF1 wrappers`).
- Public API for v1 (no auth) with a no-op dependency slot so an auth dependency can be added later without changing route signatures.
- Mocked unit tests only (no live OpenF1 calls in CI).

## Capabilities

### New Capabilities

**Foundation (must merge first, sequentially):**

- `openf1-client`: Async httpx-based client that calls OpenF1 over HTTP, translates the hybrid filter syntax to OpenF1's native operator syntax, maps upstream errors to the wrapper's error envelope, and exposes typed methods returning `list[Model]`. All endpoint capabilities depend on this.
- `app-foundation`: FastAPI app skeleton — application factory, settings/config, dependency wiring (client + service factories + auth slot), shared models (error envelope, filter base types), OpenAPI metadata (title, description, tags, servers), router registration. All endpoint capabilities depend on this.

**Endpoint wrappers (independently implementable in parallel after foundation is merged):**

- `endpoint-drivers`: `GET /v1/drivers` wrapper, `Driver` Pydantic model, `DriverService`, route with rich OpenAPI metadata.
- `endpoint-laps`: `GET /v1/laps` wrapper, `Lap` Pydantic model, `LapService`, route.
- `endpoint-meetings`: `GET /v1/meetings` wrapper, `Meeting` Pydantic model, `MeetingService`, route.
- `endpoint-sessions`: `GET /v1/sessions` wrapper, `Session` Pydantic model, `SessionService`, route.
- `endpoint-session-result`: `GET /v1/session_result` wrapper, `SessionResult` Pydantic model, `SessionResultService`, route.
- `endpoint-pit`: `GET /v1/pit` wrapper, `PitStop` Pydantic model, `PitService`, route.
- `endpoint-position`: `GET /v1/position` wrapper, `Position` Pydantic model, `PositionService`, route.
- `endpoint-overtakes`: `GET /v1/overtakes` wrapper, `Overtake` Pydantic model, `OvertakeService`, route.
- `endpoint-stints`: `GET /v1/stints` wrapper, `Stint` Pydantic model, `StintService`, route.
- `endpoint-starting-grid`: `GET /v1/starting_grid` wrapper, `StartingGridEntry` Pydantic model, `StartingGridService`, route.
- `endpoint-weather`: `GET /v1/weather` wrapper, `Weather` Pydantic model, `WeatherService`, route.
- `endpoint-championship-drivers`: `GET /v1/championship_drivers` wrapper, `ChampionshipDriver` Pydantic model, `ChampionshipDriverService`, route.
- `endpoint-championship-teams`: `GET /v1/championship_teams` wrapper, `ChampionshipTeam` Pydantic model, `ChampionshipTeamService`, route.

### Modified Capabilities

None — greenfield repo.

## Impact

- **New code**: `src/lapwise/` Python package (clients, models, services, routes, deps, config, main).
- **New tooling**: `pyproject.toml`, `uv.lock`, `.python-version`, dev dependencies (`pytest`, `pytest-asyncio`, `respx` or `pytest-httpx`, `ruff`, `mypy`).
- **New external dependency**: OpenF1 public API (`https://api.openf1.org/v1`). No API key required (historical tier).
- **No infra**: No database, no cache, no auth backend in v1.
- **No breaking changes**: Greenfield.

## Implementation Workflow

Each endpoint capability is implemented as an independent unit of work. **For every endpoint capability, follow this workflow:**

1. **Create a worktree** off `main` for the capability:
   ```bash
   git worktree add ../lapwise-<capability-name> -b feat/<capability-name>
   cd ../lapwise-<capability-name>
   ```
2. **Implement** the code per `tasks.md` for that capability.
3. **Mark tasks complete** in `tasks.md` as you go (`- [x]`).
4. **Commit** the work with a descriptive message:
   ```bash
   git add -A
   git commit -m "feat(<capability-name>): <summary>"
   ```
5. **Push** the branch:
   ```bash
   git push -u origin feat/<capability-name>
   ```
6. **Open a PR** with auto-delete of the source branch on merge:
   ```bash
   gh pr create --title "feat(<capability-name>): <summary>" --body "<body>" --delete-branch
   ```
   (If `--delete-branch` is unavailable on `gh pr create`, set repo default: `gh repo edit --delete-branch-on-merge`.)
7. **Merge** the PR:
   ```bash
   gh pr merge --squash --delete-branch
   ```
8. **Clean up** the worktree after merge:
   ```bash
   cd ../lapwise
   git worktree remove ../lapwise-<capability-name>
   ```

**Ordering constraints:**

- `openf1-client` and `app-foundation` must merge to `main` before any endpoint capability is started — endpoint capabilities import from both.
- All 13 endpoint capabilities are independent of each other and may run in parallel worktrees once the foundation is in.

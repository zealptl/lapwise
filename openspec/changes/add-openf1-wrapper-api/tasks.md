# Implementation Tasks — add-openf1-wrapper-api

**Workflow per capability** (sections 2–16 each follow this exact loop — do NOT skip steps):

```bash
# 1. From repo root, create a worktree off main
git worktree add ../lapwise-<capability> -b feat/<capability>
cd ../lapwise-<capability>/service   # all uv commands run from service/

# 2. Implement the tasks in this section
# 3. Tick each task box (- [ ] → - [x]) as you complete it in tasks.md
# 4. Commit (from repo root of the worktree)
cd ..
git add -A
git commit -m "feat(<capability>): <summary>"

# 5. Push and open PR with auto-delete of source branch on merge
git push -u origin feat/<capability>
gh pr create \
  --title "feat(<capability>): <summary>" \
  --body "Implements capability <capability> for change add-openf1-wrapper-api." \
  --base main

# 6. Merge with branch deletion
gh pr merge --squash --delete-branch --auto

# 7. Clean up worktree
cd ../lapwise
git worktree remove ../lapwise-<capability>
```

> **Ordering rule:** Section 1 (repo bootstrap) and sections 2–3 (foundation capabilities) MUST merge to `main` sequentially before sections 4–16 (endpoint capabilities) are started. Sections 4–16 are independent and SHOULD be implemented in parallel worktrees.

---

## 1. Repo bootstrap (sequential, run on `main` directly)

> One-time setup. No worktree — commit directly on `main` or via a short-lived `chore/bootstrap` branch.

- [x] 1.1 Create `.python-version` pinning Python `3.12`
- [x] 1.2 Create `pyproject.toml` with `[project]` metadata, dependencies (`fastapi`, `uvicorn[standard]`, `httpx`, `pydantic>=2`, `pydantic-settings`) and dev dependencies (`pytest`, `pytest-asyncio`, `respx`, `ruff`, `mypy`)
- [x] 1.3 Configure `[tool.ruff]` (line length, target version, lint rule selection) and `[tool.mypy]` (`strict = true` on `src/lapwise`)
- [x] 1.4 Run `uv sync` to generate `uv.lock`
- [x] 1.5 Create `src/lapwise/__init__.py` and `tests/__init__.py`
- [x] 1.6 Create `.gitignore` (Python, venv, `.idea`, `.vscode`, `.env`, `__pycache__`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `dist`, `build`)
- [x] 1.7 Create a minimal `README.md` documenting `uv sync`, `uv run uvicorn lapwise.main:app --reload`, `uv run pytest`, `uv run ruff check`, `uv run mypy src`
- [x] 1.8 Configure repo defaults: `gh repo edit --delete-branch-on-merge` (so PRs delete source branch on merge by default)
- [x] 1.9 Commit bootstrap and push to `main`

---

## 2. Capability: `openf1-client` (foundation — must merge before any endpoint capability)

> Worktree: `../lapwise-openf1-client`, branch: `feat/openf1-client`.

- [x] 2.1 Create `src/lapwise/config.py` with `Settings(pydantic-settings)`: `openf1_base_url: str = "https://api.openf1.org/v1"`, `openf1_timeout_seconds: float = 10.0`. Add `get_settings()` cached dependency.
- [x] 2.2 Create `src/lapwise/clients/errors.py` with `UpstreamError(Exception)` carrying `category: Literal["bad_gateway", "gateway_timeout", "forwarded"]`, `upstream_status: int | None`, `upstream_message: str | None`
- [x] 2.3 Create `src/lapwise/clients/filters.py`:
  - [x] 2.3.1 Translator function `translate_filters(filters: dict) -> list[tuple[str, str]]`
  - [x] 2.3.2 Handles equality (str/int/float/bool), `None` skipping, list values (repeated keys), suffixes `_lt`/`_lte`/`_gt`/`_gte` (strip suffix, emit `<`/`<=`/`>`/`>=`)
  - [x] 2.3.3 Lowercase booleans in output
- [x] 2.4 Create `src/lapwise/clients/openf1.py`:
  - [x] 2.4.1 `OpenF1Client(settings: Settings)` constructs an `httpx.AsyncClient` with timeout from settings
  - [x] 2.4.2 `async def get(path: str, model: type[T], **filters) -> list[T]`
  - [x] 2.4.3 Calls `translate_filters`, builds URL, GETs upstream
  - [x] 2.4.4 Maps `httpx.TimeoutException` → `UpstreamError("gateway_timeout", ...)`
  - [x] 2.4.5 Maps other `httpx.HTTPError` (incl. ConnectError) → `UpstreamError("bad_gateway", ...)`
  - [x] 2.4.6 If status 5xx → `UpstreamError("bad_gateway", upstream_status=..., upstream_message=truncated_body)`
  - [x] 2.4.7 If status 4xx → `UpstreamError("forwarded", upstream_status=..., upstream_message=truncated_body)`
  - [x] 2.4.8 If JSON decode fails or body is not a list → `UpstreamError("bad_gateway", upstream_message="decode failure")`
  - [x] 2.4.9 On success, parse as `[model.model_validate(item) for item in body]`
  - [x] 2.4.10 `async def aclose()` closes the underlying client
- [x] 2.5 Unit tests `tests/unit/test_filters.py`:
  - [x] 2.5.1 Equality passes through
  - [x] 2.5.2 None values skipped
  - [x] 2.5.3 Lists become repeated keys
  - [x] 2.5.4 `_lt`/`_lte`/`_gt`/`_gte` translate to `<`/`<=`/`>`/`>=`
  - [x] 2.5.5 Booleans serialize as lowercase
- [x] 2.6 Unit tests `tests/unit/test_clients_openf1.py` using `respx`:
  - [x] 2.6.1 200 returns list of parsed models
  - [x] 2.6.2 5xx raises `UpstreamError("bad_gateway")` with status preserved
  - [x] 2.6.3 4xx raises `UpstreamError("forwarded")` with status preserved
  - [x] 2.6.4 Timeout raises `UpstreamError("gateway_timeout")`
  - [x] 2.6.5 Malformed JSON raises `UpstreamError("bad_gateway")`
  - [x] 2.6.6 Filter translation is visible in the upstream URL
- [x] 2.7 `uv run ruff check`, `uv run ruff format --check`, `uv run mypy src/lapwise`, `uv run pytest tests/unit -q` all pass
- [x] 2.8 Commit, push, open PR, merge with branch deletion

---

## 3. Capability: `app-foundation` (foundation — must merge before any endpoint capability)

> Worktree: `../lapwise-app-foundation`, branch: `feat/app-foundation`. Start AFTER section 2 merges.

- [x] 3.1 Create `src/lapwise/models/common.py`:
  - [x] 3.1.1 `ErrorEnvelope` Pydantic model: `detail: str`, `upstream_status: int | None`, `upstream_message: str | None`
  - [x] 3.1.2 Document each field with `Field(description=...)`
- [x] 3.2 Create `src/lapwise/deps.py`:
  - [x] 3.2.1 `get_openf1_client(request: Request) -> OpenF1Client` returning `request.app.state.openf1_client`
  - [x] 3.2.2 `async def get_auth() -> None` (no-op slot)
  - [x] 3.2.3 Placeholder service-provider helpers wired in subsequent endpoint capabilities — leave file commented or empty stub
- [x] 3.3 Create `src/lapwise/routes/v1/__init__.py`:
  - [x] 3.3.1 `router = APIRouter(prefix="/v1", tags=["OpenF1 wrappers"], dependencies=[Depends(get_auth)])`
- [x] 3.4 Create `src/lapwise/routes/analysis/__init__.py`:
  - [x] 3.4.1 `router = APIRouter(prefix="/v1/analysis", tags=["Analysis"], dependencies=[Depends(get_auth)])` (zero routes for now)
- [x] 3.5 Create `src/lapwise/main.py`:
  - [x] 3.5.1 `lifespan` context manager that creates `OpenF1Client(get_settings())`, sets on `app.state.openf1_client`, awaits `aclose()` on shutdown
  - [x] 3.5.2 `create_app()` factory: instantiate `FastAPI(title="Lapwise — OpenF1 Wrapper API", description="...mentions wraps OpenF1 historical tier...", version="0.1.0", lifespan=lifespan, openapi_tags=[...])`
  - [x] 3.5.3 Register `GET /healthz` returning `{"status": "ok"}` (does not touch the client)
  - [x] 3.5.4 Include the v1 router and analysis router
  - [x] 3.5.5 Register exception handler for `UpstreamError` translating to `502`/`504`/forwarded status with `ErrorEnvelope` body
  - [x] 3.5.6 Configure `openapi_tags` metadata (`OpenF1 wrappers`, `Analysis`) with descriptions
  - [x] 3.5.7 Module-level `app = create_app()`
- [x] 3.6 Unit tests `tests/unit/test_app_foundation.py`:
  - [x] 3.6.1 `GET /healthz` returns 200 `{"status": "ok"}`
  - [x] 3.6.2 OpenAPI schema contains `OpenF1 wrappers` and `Analysis` tags
  - [x] 3.6.3 An `UpstreamError("bad_gateway", upstream_status=503, ...)` raised by a test route is rendered as 502 with `ErrorEnvelope` body
  - [x] 3.6.4 An `UpstreamError("gateway_timeout", ...)` is rendered as 504
  - [x] 3.6.5 An `UpstreamError("forwarded", upstream_status=404, ...)` is rendered as 404
- [x] 3.7 `uv run ruff check`, `uv run mypy src/lapwise`, `uv run pytest tests/unit -q` pass
- [x] 3.8 Commit, push, open PR, merge with branch deletion

---

## 4. Capability: `endpoint-drivers` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-drivers`, branch: `feat/endpoint-drivers`.

- [ ] 4.1 Create `src/lapwise/models/drivers.py` defining `Driver` (fields per spec)
- [ ] 4.2 Create `src/lapwise/services/drivers.py` defining `DriverService.list_drivers(**filters) -> list[Driver]`
- [ ] 4.3 Add `get_driver_service` provider in `src/lapwise/deps.py`
- [ ] 4.4 Create `src/lapwise/routes/v1/drivers.py`:
  - [ ] 4.4.1 `GET /drivers` returning `list[Driver]`
  - [ ] 4.4.2 Typed query params: `driver_number: list[int] | None`, `session_key: int | str | None`, `meeting_key: int | str | None`, plus other OpenF1-documented equality fields
  - [ ] 4.4.3 `summary`, multi-paragraph `description` linking to OpenF1 docs, per-`Query` descriptions/examples
  - [ ] 4.4.4 `responses` dict with examples for 200/422/502/504
- [ ] 4.5 Register `routes/v1/drivers.router` in `routes/v1/__init__.py`
- [ ] 4.6 Unit tests:
  - [ ] 4.6.1 `tests/unit/test_services_drivers.py` — service forwards filters and returns parsed list (client mocked)
  - [ ] 4.6.2 `tests/unit/test_routes_drivers.py` — TestClient with mocked service: equality filter, repeated `driver_number` becomes list[int], 502 path
- [ ] 4.7 `uv run ruff check`, `uv run mypy src/lapwise`, `uv run pytest tests/unit -q` pass
- [ ] 4.8 Commit, push, open PR, merge with branch deletion

---

## 5. Capability: `endpoint-laps` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-laps`, branch: `feat/endpoint-laps`.

- [ ] 5.1 Create `src/lapwise/models/laps.py` defining `Lap` (fields per spec)
- [ ] 5.2 Create `src/lapwise/services/laps.py` defining `LapService.list_laps(**filters) -> list[Lap]`
- [ ] 5.3 Add `get_lap_service` provider in `src/lapwise/deps.py`
- [ ] 5.4 Create `src/lapwise/routes/v1/laps.py`:
  - [ ] 5.4.1 `GET /laps` returning `list[Lap]`
  - [ ] 5.4.2 Typed query params including comparison suffixes: `lap_duration_lt`, `lap_duration_lte`, `lap_duration_gt`, `lap_duration_gte`, `lap_number`, `driver_number: list[int] | None`, `session_key`, `meeting_key`, `is_pit_out_lap`
  - [ ] 5.4.3 Rich OpenAPI metadata (summary, description with OpenF1 link, param descriptions, examples)
  - [ ] 5.4.4 `responses` dict with examples for 200/422/502/504
- [ ] 5.5 Register `routes/v1/laps.router` in `routes/v1/__init__.py`
- [ ] 5.6 Unit tests:
  - [ ] 5.6.1 `tests/unit/test_services_laps.py` — service forwards filters
  - [ ] 5.6.2 `tests/unit/test_routes_laps.py` — equality and comparison suffix filters; verify the upstream URL captured by the mocked client contains `lap_duration<...`
- [ ] 5.7 `uv run ruff check`, `uv run mypy src/lapwise`, `uv run pytest tests/unit -q` pass
- [ ] 5.8 Commit, push, open PR, merge with branch deletion

---

## 6. Capability: `endpoint-meetings` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-meetings`, branch: `feat/endpoint-meetings`.

- [ ] 6.1 Create `src/lapwise/models/meetings.py` defining `Meeting` (fields per spec)
- [ ] 6.2 Create `src/lapwise/services/meetings.py` defining `MeetingService.list_meetings(**filters) -> list[Meeting]`
- [ ] 6.3 Add `get_meeting_service` provider in `src/lapwise/deps.py`
- [ ] 6.4 Create `src/lapwise/routes/v1/meetings.py`:
  - [ ] 6.4.1 `GET /meetings` returning `list[Meeting]`
  - [ ] 6.4.2 Typed query params including `meeting_key: int | Literal["latest"] | None`, `year`, `country_name`, `circuit_short_name`, `location`
  - [ ] 6.4.3 Rich OpenAPI metadata + responses examples
- [ ] 6.5 Register `routes/v1/meetings.router` in `routes/v1/__init__.py`
- [ ] 6.6 Unit tests for service and route, including the `latest` literal pass-through
- [ ] 6.7 Lint, type-check, tests pass
- [ ] 6.8 Commit, push, open PR, merge with branch deletion

---

## 7. Capability: `endpoint-sessions` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-sessions`, branch: `feat/endpoint-sessions`.

- [ ] 7.1 Create `src/lapwise/models/sessions.py` defining `Session`
- [ ] 7.2 Create `src/lapwise/services/sessions.py` defining `SessionService.list_sessions`
- [ ] 7.3 Add `get_session_service` provider in `src/lapwise/deps.py`
- [ ] 7.4 Create `src/lapwise/routes/v1/sessions.py` with `GET /sessions`, `session_key: int | Literal["latest"] | None`, `meeting_key`, `country_name`, `session_name`, `session_type`, `year`, plus rich OpenAPI metadata
- [ ] 7.5 Register router
- [ ] 7.6 Unit tests for service and route incl. `latest` pass-through
- [ ] 7.7 Lint, type-check, tests pass
- [ ] 7.8 Commit, push, open PR, merge with branch deletion

---

## 8. Capability: `endpoint-session-result` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-session-result`, branch: `feat/endpoint-session-result`.

- [ ] 8.1 Create `src/lapwise/models/session_result.py` defining `SessionResult` with Union types for `duration` and `gap_to_leader`
- [ ] 8.2 Create `src/lapwise/services/session_result.py` defining `SessionResultService.list_results`
- [ ] 8.3 Add `get_session_result_service` provider in `src/lapwise/deps.py`
- [ ] 8.4 Create `src/lapwise/routes/v1/session_result.py` with `GET /session_result`, params: `session_key`, `meeting_key`, `driver_number: list[int] | None`, `position`, `position_lt`, `position_lte`, `position_gt`, `position_gte`, `dnf`, `dns`, `dsq`. Rich OpenAPI metadata with a `200` example whose row uses the array form of `duration`
- [ ] 8.5 Register router
- [ ] 8.6 Unit tests for service and route incl. `position_lte` translating to `position<=3`
- [ ] 8.7 Lint, type-check, tests pass
- [ ] 8.8 Commit, push, open PR, merge with branch deletion

---

## 9. Capability: `endpoint-pit` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-pit`, branch: `feat/endpoint-pit`.

- [ ] 9.1 Create `src/lapwise/models/pit.py` defining `PitStop`
- [ ] 9.2 Create `src/lapwise/services/pit.py` defining `PitService.list_pit_stops`
- [ ] 9.3 Add `get_pit_service` provider in `src/lapwise/deps.py`
- [ ] 9.4 Create `src/lapwise/routes/v1/pit.py` with `GET /pit`, params: `session_key`, `meeting_key`, `driver_number: list[int] | None`, `lap_number`, `stop_duration_lt`, `stop_duration_lte`, `stop_duration_gt`, `stop_duration_gte`. Rich OpenAPI metadata
- [ ] 9.5 Register router
- [ ] 9.6 Unit tests for service and route incl. `stop_duration_lt` translation
- [ ] 9.7 Lint, type-check, tests pass
- [ ] 9.8 Commit, push, open PR, merge with branch deletion

---

## 10. Capability: `endpoint-position` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-position`, branch: `feat/endpoint-position`.

- [ ] 10.1 Create `src/lapwise/models/position.py` defining `Position`
- [ ] 10.2 Create `src/lapwise/services/position.py` defining `PositionService.list_positions`
- [ ] 10.3 Add `get_position_service` provider in `src/lapwise/deps.py`
- [ ] 10.4 Create `src/lapwise/routes/v1/position.py` with `GET /position`, params: `session_key`, `meeting_key`, `driver_number: list[int] | None`, `position`, `position_lt`, `position_lte`, `position_gt`, `position_gte`. Rich OpenAPI metadata
- [ ] 10.5 Register router
- [ ] 10.6 Unit tests for service and route incl. `position_lte` translation
- [ ] 10.7 Lint, type-check, tests pass
- [ ] 10.8 Commit, push, open PR, merge with branch deletion

---

## 11. Capability: `endpoint-overtakes` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-overtakes`, branch: `feat/endpoint-overtakes`.

- [ ] 11.1 Create `src/lapwise/models/overtakes.py` defining `Overtake`
- [ ] 11.2 Create `src/lapwise/services/overtakes.py` defining `OvertakeService.list_overtakes`
- [ ] 11.3 Add `get_overtake_service` provider in `src/lapwise/deps.py`
- [ ] 11.4 Create `src/lapwise/routes/v1/overtakes.py` with `GET /overtakes`, params: `session_key`, `meeting_key`, `overtaking_driver_number`, `overtaken_driver_number`, `position`. Rich OpenAPI metadata noting race-only / incomplete data
- [ ] 11.5 Register router
- [ ] 11.6 Unit tests for service and route
- [ ] 11.7 Lint, type-check, tests pass
- [ ] 11.8 Commit, push, open PR, merge with branch deletion

---

## 12. Capability: `endpoint-stints` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-stints`, branch: `feat/endpoint-stints`.

- [ ] 12.1 Create `src/lapwise/models/stints.py` defining `Stint`
- [ ] 12.2 Create `src/lapwise/services/stints.py` defining `StintService.list_stints`
- [ ] 12.3 Add `get_stint_service` provider in `src/lapwise/deps.py`
- [ ] 12.4 Create `src/lapwise/routes/v1/stints.py` with `GET /stints`, params: `session_key`, `meeting_key`, `driver_number: list[int] | None`, `stint_number`, `compound`, `tyre_age_at_start`, `tyre_age_at_start_lt`, `tyre_age_at_start_lte`, `tyre_age_at_start_gt`, `tyre_age_at_start_gte`. Rich OpenAPI metadata
- [ ] 12.5 Register router
- [ ] 12.6 Unit tests for service and route incl. `tyre_age_at_start_gte` translation
- [ ] 12.7 Lint, type-check, tests pass
- [ ] 12.8 Commit, push, open PR, merge with branch deletion

---

## 13. Capability: `endpoint-starting-grid` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-starting-grid`, branch: `feat/endpoint-starting-grid`.

- [ ] 13.1 Create `src/lapwise/models/starting_grid.py` defining `StartingGridEntry`
- [ ] 13.2 Create `src/lapwise/services/starting_grid.py` defining `StartingGridService.list_grid`
- [ ] 13.3 Add `get_starting_grid_service` provider in `src/lapwise/deps.py`
- [ ] 13.4 Create `src/lapwise/routes/v1/starting_grid.py` with `GET /starting_grid`, params: `session_key`, `meeting_key`, `driver_number: list[int] | None`, `position`, `position_lt`, `position_lte`, `position_gt`, `position_gte`. Rich OpenAPI metadata
- [ ] 13.5 Register router
- [ ] 13.6 Unit tests for service and route incl. `position_lte` translation
- [ ] 13.7 Lint, type-check, tests pass
- [ ] 13.8 Commit, push, open PR, merge with branch deletion

---

## 14. Capability: `endpoint-weather` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-weather`, branch: `feat/endpoint-weather`.

- [ ] 14.1 Create `src/lapwise/models/weather.py` defining `Weather`
- [ ] 14.2 Create `src/lapwise/services/weather.py` defining `WeatherService.list_weather`
- [ ] 14.3 Add `get_weather_service` provider in `src/lapwise/deps.py`
- [ ] 14.4 Create `src/lapwise/routes/v1/weather.py` with `GET /weather`, params: `session_key`, `meeting_key`, plus comparison suffixes for `air_temperature`, `track_temperature`, `humidity`, `pressure`, `rainfall`, `wind_speed`, `wind_direction`. Rich OpenAPI metadata
- [ ] 14.5 Register router
- [ ] 14.6 Unit tests for service and route incl. multiple `_gte` filters translated together
- [ ] 14.7 Lint, type-check, tests pass
- [ ] 14.8 Commit, push, open PR, merge with branch deletion

---

## 15. Capability: `endpoint-championship-drivers` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-championship-drivers`, branch: `feat/endpoint-championship-drivers`.

- [ ] 15.1 Create or extend `src/lapwise/models/championship.py` defining `ChampionshipDriver`
- [ ] 15.2 Create `src/lapwise/services/championship.py` (or extend) defining `ChampionshipDriverService.list_standings`
- [ ] 15.3 Add `get_championship_driver_service` provider in `src/lapwise/deps.py`
- [ ] 15.4 Create `src/lapwise/routes/v1/championship_drivers.py` with `GET /championship_drivers`, params: `session_key: int | Literal["latest"] | None`, `meeting_key: int | Literal["latest"] | None`, `driver_number: list[int] | None`. Rich OpenAPI metadata noting beta / race-only
- [ ] 15.5 Register router
- [ ] 15.6 Unit tests for service and route incl. repeated `driver_number`
- [ ] 15.7 Lint, type-check, tests pass
- [ ] 15.8 Commit, push, open PR, merge with branch deletion

---

## 16. Capability: `endpoint-championship-teams` (parallel — start after section 3 merges)

> Worktree: `../lapwise-endpoint-championship-teams`, branch: `feat/endpoint-championship-teams`.

- [ ] 16.1 Create or extend `src/lapwise/models/championship.py` defining `ChampionshipTeam`
- [ ] 16.2 Create or extend `src/lapwise/services/championship.py` defining `ChampionshipTeamService.list_standings`
- [ ] 16.3 Add `get_championship_team_service` provider in `src/lapwise/deps.py`
- [ ] 16.4 Create `src/lapwise/routes/v1/championship_teams.py` with `GET /championship_teams`, params: `session_key: int | Literal["latest"] | None`, `meeting_key: int | Literal["latest"] | None`, `team_name`. Rich OpenAPI metadata noting beta / race-only
- [ ] 16.5 Register router
- [ ] 16.6 Unit tests for service and route
- [ ] 16.7 Lint, type-check, tests pass
- [ ] 16.8 Commit, push, open PR, merge with branch deletion

---

## 17. Final integration check (sequential — run on `main` after all endpoint capabilities merge)

- [ ] 17.1 Pull `main` locally
- [ ] 17.2 `uv sync`
- [ ] 17.3 `uv run pytest tests/unit -q` — full suite green
- [ ] 17.4 `uv run ruff check`, `uv run ruff format --check`, `uv run mypy src/lapwise` — all clean
- [ ] 17.5 `uv run uvicorn lapwise.main:app` — manually spot-check `/docs` shows all 13 endpoints under `OpenF1 wrappers` tag with rich descriptions and examples
- [ ] 17.6 Verify `/openapi.json` includes `502` and `504` response shapes for every wrapper endpoint

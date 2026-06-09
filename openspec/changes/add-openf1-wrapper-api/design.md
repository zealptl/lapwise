## Context

OpenF1 (`https://api.openf1.org/v1`) is an open-source public API for Formula 1 telemetry, timing, and session data. Historical data (2023 onwards) is free; real-time requires a paid subscription. We are building a Python 3.12 FastAPI backend that wraps OpenF1's historical tier so that:

1. We can publish a stable, richly documented OpenAPI contract that we own.
2. We can introduce a service layer between routes and the OpenF1 HTTP client, so future derived endpoints (analytics, transformations) can compose existing services without leaking HTTP concerns into route handlers.
3. Endpoint paths under `/v1/*` mirror OpenF1's paths so client behavior is familiar; the only intentional divergence from OpenF1's surface is the **comparison filter syntax** (see Decisions).

Greenfield repo. No prior code, no infra. Package manager: `uv`. Python: 3.12.

## Goals / Non-Goals

**Goals:**

- 13 wrapper endpoints under `/v1/*` mirroring the 13 OpenF1 endpoints from `docs/openf1.md`.
- Layered architecture: `routes/` → `services/` → `clients/openf1.py`. Each layer is independently testable.
- All responses returned as typed Pydantic models that mirror OpenF1's raw response shapes (Union types where OpenF1 itself is messy).
- Hybrid filter syntax: equality and repeated-key `in` filters mirror OpenF1 exactly; comparisons use `_lt` / `_lte` / `_gt` / `_gte` suffixes.
- Standardized upstream error mapping: OpenF1 5xx → 502, timeout → 504, 4xx forwarded.
- Rich OpenAPI documentation per endpoint: summary, description, per-parameter descriptions, response model with field descriptions, success and error examples, tags.
- Mocked unit tests across client, services, and routes. No live HTTP calls in CI.
- Capability-sized work units that can be implemented in parallel worktrees once the foundation is merged.

**Non-Goals:**

- Real-time / paid-tier OpenF1 endpoints (no token pass-through, no SSE, no WebSocket).
- Caching of any kind in v1.
- Authentication on the wrapper API (a no-op dependency slot is provided for later).
- Derived/analytics endpoints (the `/v1/analysis/*` router is reserved, no endpoints in this change).
- Live integration tests against OpenF1 in CI.
- Deployment configuration (Dockerfile, IaC, etc.).
- OpenF1 endpoints not in `docs/openf1.md` (e.g. `car_data`, `intervals`, `location`, `race_control`, `team_radio`).

## Decisions

### D1. Layered architecture

```
routes/  →  services/  →  clients/openf1.py  →  api.openf1.org/v1
```

- **Routes**: FastAPI path operation functions. Own input validation (typed query params), OpenAPI metadata, response model. No HTTP, no business logic.
- **Services**: One service class per resource (`DriverService`, `LapService`, …). In v1 each service is a thin orchestrator that delegates to `OpenF1Client`. Designed so future derived endpoints can compose multiple services (e.g. `RacePaceService` reading from `LapService` + `StintService`).
- **Client**: One `OpenF1Client` that owns the `httpx.AsyncClient`, filter-syntax translation, and upstream-error mapping.

**Alternatives considered:** (a) Skip services and call the client directly from routes — rejected because future derived endpoints would have to duplicate orchestration. (b) Merge services into a single facade — rejected because per-resource services give cleaner unit-test boundaries and follow how the data is naturally partitioned.

### D2. Hybrid filter syntax

OpenF1 supports a non-standard query syntax (`?stop_duration<2.3`, `?position<=3`, repeated keys like `?driver_number=4&driver_number=81`). FastAPI cannot natively bind `field<value` to function parameters. We choose:

- **Equality**: `?driver_number=4` — exposed as a typed query param. Mirror of OpenF1.
- **Repeated-key `in` filter**: `?driver_number=4&driver_number=81` — exposed as `list[int]`. Mirror of OpenF1.
- **Comparisons**: `?stop_duration_lt=2.3`, `?position_lte=3`, `?wind_direction_gte=130` — uses suffixes `_lt`, `_lte`, `_gt`, `_gte`. **Diverges from OpenF1** so the params are typed and visible in OpenAPI.

`OpenF1Client` translates these back to OpenF1's native syntax when building the upstream URL:

```
stop_duration_lt=2.3  →  stop_duration<2.3
position_lte=3        →  position<=3
wind_direction_gte=130 →  wind_direction>=130
driver_number=[4,81]  →  driver_number=4&driver_number=81
```

Translation lives in `clients/filters.py` so it can be unit-tested without HTTP.

**Alternatives considered:** (a) Mirror OpenF1 syntax exactly — rejected because OpenAPI cannot type `field<value`. (b) Normalize all filters (including equality) to `_eq` suffixes — rejected because it gives no benefit over the hybrid choice and breaks intuitive URLs. (c) Generic `?filter=` DSL — rejected because OpenAPI cannot introspect individual fields.

### D3. Mirror OpenF1's response shapes verbatim

Pydantic models mirror OpenF1's documented response fields, including its messiness:

- `gap_to_leader: float | str | None` (OpenF1 returns `+1 LAP` strings).
- `SessionResult.duration: float | list[float] | None` (qualifying returns three values for Q1/Q2/Q3).
- `is_pit_out_lap: bool | None` (some sessions omit it).
- Optional fields default to `None` rather than raising.

Reasoning: this is the wrapper layer. Normalization belongs in future derived endpoints where the meaning of "clean" depends on the use case. Mirroring keeps the contract honest about upstream behavior.

**Alternatives considered:** (a) Normalize at the wrapper — rejected because it forces a single normalization choice on every consumer. (b) Per-session-type result models — deferred to a future derived endpoint that needs the clean shape.

### D4. Error mapping

`OpenF1Client` maps upstream conditions to wrapper responses:

| Upstream condition | Wrapper response | Notes |
|---|---|---|
| 2xx | 200 with payload | — |
| Upstream 4xx | Same status, structured envelope | Forward 404, 422, 429 as-is |
| Upstream 5xx | 502 Bad Gateway | OpenF1 was down or broken |
| Network timeout | 504 Gateway Timeout | `httpx.TimeoutException` |
| Network error (DNS, conn refused) | 502 Bad Gateway | `httpx.ConnectError` etc. |
| JSON decode failure | 502 Bad Gateway | Upstream returned bad payload |

Error envelope:

```json
{
  "detail": "OpenF1 upstream error",
  "upstream_status": 503,
  "upstream_message": "<text>"
}
```

For wrapper-side validation failures (bad query param), FastAPI's default 422 with its detail format is kept — not wrapped.

### D5. Rich OpenAPI metadata convention

Every wrapper route uses:

- `summary=` — one-line description.
- `description=` — multi-paragraph; includes a link to the OpenF1 source endpoint (`https://api.openf1.org/v1/<path>`).
- `tags=["OpenF1 wrappers"]`.
- `response_model=list[Model]`.
- `responses={200: {...with example}, 422: ..., 502: ..., 504: ...}` — example payloads for each.
- Each query param uses `Query(..., description="...", example=..., title=...)`.
- Each Pydantic model field uses `Field(..., description="...", examples=[...])`.

Per-endpoint OpenAPI lives next to the route in `routes/v1/<resource>.py`, not in a central place — keeps each endpoint capability self-contained.

### D6. Async throughout

- `httpx.AsyncClient` in `OpenF1Client`.
- All services `async def`.
- All route handlers `async def`.

FastAPI handles sync handlers in a thread pool, but async-throughout means we avoid blocking the event loop and we're ready for concurrent fan-out in future derived endpoints (e.g. `await asyncio.gather(...)` across services).

### D7. Dependency injection via FastAPI Depends

- `get_settings()` returns cached `Settings`.
- `get_openf1_client()` returns a process-wide `OpenF1Client` (created at app startup via lifespan).
- `get_<resource>_service()` returns a fresh service instance wrapping the shared client.
- `get_auth()` — currently a no-op dep returning `None`. Wired into the v1 router as `dependencies=[Depends(get_auth)]` so later swap-in is one-line.

### D8. Project layout

```
lapwise/
  pyproject.toml          (uv-managed, Python 3.12)
  uv.lock
  .python-version         (3.12)
  README.md
  src/lapwise/
    __init__.py
    main.py               (FastAPI app, OpenAPI metadata, lifespan, router registration)
    config.py             (Settings via pydantic-settings)
    deps.py               (DI providers: client, services, auth slot)
    clients/
      __init__.py
      openf1.py           (OpenF1Client)
      filters.py          (hybrid filter → OpenF1 query-string translator)
      errors.py           (UpstreamError, mapping helpers)
    models/
      __init__.py
      common.py           (ErrorEnvelope, shared types)
      drivers.py          (Driver)
      laps.py             (Lap)
      meetings.py         (Meeting)
      sessions.py         (Session)
      session_result.py   (SessionResult)
      pit.py              (PitStop)
      position.py         (Position)
      overtakes.py        (Overtake)
      stints.py           (Stint)
      starting_grid.py    (StartingGridEntry)
      weather.py          (Weather)
      championship.py     (ChampionshipDriver, ChampionshipTeam)
    services/
      __init__.py
      base.py             (BaseService — shared protocol/helpers)
      drivers.py, laps.py, meetings.py, sessions.py, session_result.py,
      pit.py, position.py, overtakes.py, stints.py, starting_grid.py,
      weather.py, championship.py
    routes/
      __init__.py
      v1/
        __init__.py       (APIRouter prefix="/v1", tags=["OpenF1 wrappers"])
        drivers.py, laps.py, meetings.py, sessions.py, session_result.py,
        pit.py, position.py, overtakes.py, stints.py, starting_grid.py,
        weather.py, championship_drivers.py, championship_teams.py
      analysis/
        __init__.py       (APIRouter prefix="/v1/analysis", tags=["Analysis"])
                          (no endpoints in this change — slot for future work)
  tests/
    __init__.py
    conftest.py           (shared fixtures: mocked client, app, TestClient)
    unit/
      test_clients_openf1.py
      test_filters.py
      test_errors.py
      test_services_<resource>.py     (one per resource)
      test_routes_<resource>.py       (one per resource)
```

### D9. Tooling

- **Package manager**: `uv` (lockfile `uv.lock`).
- **Runtime deps**: `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic` (v2), `pydantic-settings`.
- **Dev deps**: `pytest`, `pytest-asyncio`, `respx` (mocks `httpx`), `ruff` (lint + format), `mypy`.
- **Lint/format**: `ruff check` + `ruff format`.
- **Type check**: `mypy src/lapwise --strict` (best effort; relax per-module if needed).
- **Test**: `pytest tests/unit -q`.

### D10. Parallel implementation workflow

Per the proposal's Implementation Workflow section, each capability is implemented in its own git worktree off `main`, on a branch `feat/<capability-name>`, merged via PR with branch deletion. Foundation capabilities (`openf1-client`, `app-foundation`) must merge before endpoint capabilities can start, because endpoint capabilities import from them. The 13 endpoint capabilities are independent and may proceed in parallel worktrees once the foundation is merged.

## Risks / Trade-offs

- **OpenF1 contract drift**: OpenF1 is a community project and may change response shapes without notice. → Mitigation: Union types absorb mild drift; mocked tests pin our parsing; we'll catch breakages at runtime (502 from JSON decode failure) rather than silently corrupting data.
- **No caching means we hammer OpenF1 under load**: If our API gets traffic, every request hits OpenF1. → Mitigation: documented as a known gap; add cache in a follow-up before any public deploy.
- **Hybrid filter divergence from OpenF1**: Clients that already know OpenF1 will be surprised by `_lt`/`_gte` instead of `<`/`>=`. → Mitigation: rich OpenAPI documentation per endpoint makes the convention discoverable; comparison filters are the less-common case.
- **Mocked-only tests can mask OpenF1 contract drift**: Unit tests will keep passing even if OpenF1 changes its shape. → Mitigation: accepted for v1 speed. Plan a follow-up to add recorded integration tests before public deploy.
- **Capability granularity creates merge friction**: 13 parallel branches all touching `main.py` (to register routers) and `deps.py` (to register service providers) could conflict. → Mitigation: foundation merge establishes the registration pattern; each endpoint capability adds one line to `main.py` (router include) and one provider to `deps.py`. Reviewers should expect trivial merge resolution. If conflicts become annoying, switch to a router-auto-discovery pattern in a follow-up.

## Migration Plan

Greenfield — no migration. Deploy is out of scope for this change.

## Open Questions

- None identified. All major decisions were explicitly chosen during exploration (see proposal).

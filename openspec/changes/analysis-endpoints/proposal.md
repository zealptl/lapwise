## Why

Lapwise exposes raw F1 telemetry from OpenF1 but provides no derived intelligence — callers must aggregate data across multiple endpoints and sessions themselves. The upcoming AI agent (`lapwise-f1-agent`) needs computed analytics it can reason over directly; exposing raw data forces the LLM to do complex multi-step computation which is slow, expensive, and error-prone.

## What Changes

- **8 new analysis endpoints** under `/v1/analysis/` that aggregate, normalize, and score F1 data into agent-ready metrics
- **1 new static prices endpoint** under `/v1/fantasy/prices` returning 2025 driver and constructor prices for the official F1 Fantasy game
- **1 new shared utility module** (`services/analysis/common.py`) for meeting and session resolution used by all analysis endpoints
- All new endpoints follow existing auth, response envelope, and error conventions

## Capabilities

### New Capabilities

- `analysis-common`: Shared utility for resolving last-N meetings and filtering sessions by type — used by all analysis endpoints to avoid code duplication
- `analysis-driver-pace-profile`: Qualification pace (Qpace) and race pace (Rpace) per driver, with sector deltas, trend direction, and overtake adjustment
- `analysis-dnf-rates`: DNF/DNS/DSQ rates per driver across competitive sessions (Qualifying, Race, Sprint), broken down by session type
- `analysis-fastest-lap-candidates`: Fastest lap probability per driver based on historical FL occurrence in race and sprint sessions
- `analysis-overtake-profile`: Offensive and defensive overtake stats per driver in race and sprint sessions, with aggression score
- `analysis-circuit-profile`: Circuit DNA — overtake difficulty, qualifying importance index, safety car tendency, tyre compound usage, weather variability, and typical pit stop count
- `analysis-championship-context`: Per-driver and per-constructor momentum, desperation index, and battle flags based on points trajectory
- `analysis-qualifying-trends`: Sector dominance, Q2/Q3 appearance rates, and grid performance vs championship position per driver
- `analysis-constructor-pitstop`: Constructor pit stop speed distribution, fantasy points yield, fastest pitstop rate, and consistency score
- `fantasy-prices`: Static 2025 F1 Fantasy driver and constructor price list

### Modified Capabilities

_(none — no existing spec-level requirements change)_

## Impact

- **New routes**: 9 new FastAPI routes across `routes/v1/analysis/` and `routes/v1/fantasy/`
- **New services**: 9 new service modules in `services/analysis/` plus `services/fantasy/`
- **New models**: Pydantic response models for each analysis endpoint and the prices list
- **New shared utility**: `services/analysis/common.py` — `get_last_n_meeting_keys()` and `get_sessions_for_meetings()` used by all analysis services
- **OpenF1 client**: No changes needed — analysis services compose existing client calls
- **No breaking changes** to existing endpoints
- **Dependencies**: All data sourced from existing OpenF1 endpoints already wrapped by the client (`/meetings`, `/sessions`, `/laps`, `/stints`, `/pit`, `/overtakes`, `/position`, `/starting_grid`, `/session_result`, `/championship_drivers`, `/championship_teams`, `/weather`)

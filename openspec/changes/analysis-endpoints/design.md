## Context

Lapwise is a FastAPI service (Python) deployed on AWS Lambda + API Gateway with Cognito auth. It wraps the OpenF1 public API via a typed client (`clients/openf1.py`). All existing endpoints follow the same pattern: route → service → OpenF1 client → Pydantic model.

The analysis endpoints aggregate data across multiple sessions and meetings, requiring fan-out calls to the OpenF1 client. The `lapwise-f1-agent` change (separate CDK stack) will consume these endpoints as tools via AgentCore Gateway.

## Goals / Non-Goals

**Goals:**
- Add 8 computed analysis endpoints and 1 static prices endpoint
- Share meeting/session resolution logic across all analysis endpoints via a common utility
- Keep all endpoints composable — inputs are explicit, outputs are deterministic given the same inputs
- Follow existing FastAPI route/service/model conventions exactly

**Non-Goals:**
- Caching (deferred — all calls go fresh to OpenF1)
- Real-time or streaming responses
- Writing back to any store
- Fetching driver/constructor prices dynamically (static JSON for now)

## Decisions

### Decision 1: Shared `analysis/common.py` utility over per-endpoint duplication

All 8 analysis endpoints need to resolve "last N meetings" and "sessions of type X within those meetings." This requires: fetch all meetings → sort by date → take last N → fetch sessions per meeting → filter by session_type.

**Chosen**: Single `services/analysis/common.py` with two async functions:
- `get_last_n_meeting_keys(client, n, year, circuit_key, year_range)` — returns `list[int]`
- `get_sessions_for_meetings(client, meeting_keys, session_types)` — returns `list[Session]`

**Alternative considered**: Inline per service. Rejected — duplication of ~30 lines of sorting/filtering logic across 8 services, divergence risk.

### Decision 2: `last_n_races` means last N **meetings** (race weekends), not sessions

A meeting is a race weekend (Practice + Qualifying + Race, optionally Sprint). "12 races" = 12 meetings. Each analysis endpoint specifies which session_types it pulls from within each meeting.

**Rationale**: A sprint weekend has more sessions but is still one race weekend. Counting sessions would produce inconsistent windows depending on how many sprint weekends fall in the sample.

### Decision 3: `include_circuit_history` fetches same circuit, last 2 calendar years

When `include_circuit_history=True`, the utility fetches all meetings at the same `circuit_key` for `(current_year - 2, current_year - 1)` and merges them with the current-season meetings. Deduplication by `meeting_key`.

**Rationale**: Circuit-specific history improves predictions for street circuits (Monaco, Singapore) and high-altitude venues where OpenF1 current-season data may be sparse early in the year.

### Decision 4: Safety car / VSC lap exclusion via 110% median threshold

We have no SC flag in OpenF1 data. Laps where `lap_duration > 1.1 * session_median_lap_duration` are excluded from pace calculations.

**Rationale**: Any lap >10% slower than the session median is either behind a SC/VSC, a heavily damaged car, or a slow-in lap. All are unrepresentative of true race pace. Threshold of 110% is conservative — real racing laps rarely deviate this much.

**Alternative considered**: Exclude laps where `position` time-series shows no change (SC periods). Rejected — requires expensive join of position time-series with lap data and still doesn't cleanly identify VSC periods.

### Decision 5: Rpace computed from "prime window" laps only (tyre_age 3–15)

Clean-air race pace is computed from laps where:
- `is_pit_out_lap = False`
- `lap_number > 1` (lap 1 excluded — traffic/standing start)
- `lap_duration` is not null
- `lap_duration <= 1.1 * session_median` (SC exclusion)
- Tyre age (from stints join): `3 <= tyre_age <= 15`

**Rationale**: Laps 0–2 on a tyre are "push laps" (unrepresentative high performance). Laps 16+ show heavy degradation. The 3–15 window captures stable representative pace.

### Decision 6: Exponential decay weighting for Qpace and trend scores

Position scores across meetings are weighted with `weight = 0.85 ^ i` where `i=0` is the most recent meeting.

**Rationale**: Matches the analyst's approach — recent performance is more predictive than older data. A driver who was P1 last race matters more than P1 six months ago. Decay factor 0.85 gives the most recent race ~2.5x the weight of a race 8 rounds ago.

### Decision 7: Overtake data quality — no warning field

The OpenF1 overtakes endpoint notes data may be incomplete. We do not surface a `data_quality_warning` field. The agent system prompt will carry general awareness that overtake data is directionally useful but not perfectly complete.

### Decision 8: Constructor pitstop analysis uses `stop_duration` not `lane_duration`

`stop_duration` = stationary stop time (what teams optimize for, what F1 Fantasy scores).
`lane_duration` = total time in pit lane (includes entry/exit, not scored by F1 Fantasy).

Fantasy scoring brackets apply to `stop_duration`. Both fields are returned in the response for completeness.

### Decision 9: Fantasy prices as hardcoded JSON in the route layer

2025 driver and constructor prices are stored as a Python dict in `routes/v1/fantasy/prices.py`. Updated manually after each race when prices change.

**Alternative considered**: SSM Parameter Store or DynamoDB. Rejected for now — prices change at most 24 times per season (after each race). A code deploy is acceptable overhead for this phase.

## Risks / Trade-offs

- **OpenF1 fan-out latency**: Analysis endpoints may issue 12–36 sequential OpenF1 calls (one per meeting/session). Lambda timeout is 29s (API Gateway limit). Risk of timeout for wide windows. → Mitigation: add asyncio.gather() for parallel session fetches per meeting. Monitor p99 latency after launch.
- **OpenF1 rate limits**: No published rate limit, but rapid fan-out may trigger throttling. → Mitigation: add exponential backoff in the OpenF1 client error handler (already has error handling via `clients/errors.py`).
- **Stale prices**: Static JSON prices go stale after each race. → Mitigation: comment in the file with the date last updated; add a TODO for dynamic pricing in a future change.
- **Sparse data for new drivers/circuits**: A driver who joined mid-season may have fewer than 12 races. `sample_races` field in each response lets the agent know how much data backed the score.

## Open Questions

- Should analysis endpoints require auth (Cognito) like the rest of Lapwise, or be public? → Default: same Cognito auth as all other endpoints. The AgentCore Gateway holds its own M2M credentials.
- Should `last_n_races` have a maximum cap (e.g., 24) to prevent excessive fan-out? → Leave uncapped for now, monitor in production.

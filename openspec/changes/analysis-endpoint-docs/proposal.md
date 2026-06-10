## Why

The 8 analysis endpoints and the fantasy prices endpoint were implemented without the documentation pattern established by the existing v1 wrapper endpoints — no `_DESCRIPTION` prose, no `_RESPONSES` dicts with examples, and terse one-line `Query` descriptions. Developers hitting these endpoints via Swagger UI or the OpenAPI spec have no clear explanation of what the computed fields represent.

## What Changes

- Add a `_DESCRIPTION` block to each of the 9 route files explaining what the endpoint computes and what the response fields mean at a high level (1–2 sentences per field)
- Add a `_RESPONSES` dict covering 200 (with a realistic example payload), 422, 502, and 504 to each route
- Expand terse `Query(description=...)` strings to match the detail level of the wrapper endpoints
- Add a `summary=` string to the routes that are missing one (`driver_pace`, `dnf_rates`, `overtake_profile`, `constructor_pitstop`)

## Capabilities

### New Capabilities

- `analysis-endpoint-docs`: Documentation enrichment for all 9 analysis/fantasy route files — `_DESCRIPTION`, `_RESPONSES`, expanded `Query` descriptions, and `summary=` strings following the established wrapper endpoint pattern

### Modified Capabilities

<!-- No existing spec-level behavior is changing — this is documentation only -->

## Impact

- 9 route files modified: `routes/v1/analysis/{driver_pace,dnf_rates,fastest_lap,overtake_profile,circuit_profile,championship_context,qualifying_trends,constructor_pitstop}.py` and `routes/v1/fantasy/prices.py`
- No behavior changes, no model changes, no service changes
- Swagger UI at `/docs` becomes significantly more useful for the agent and any human consumers

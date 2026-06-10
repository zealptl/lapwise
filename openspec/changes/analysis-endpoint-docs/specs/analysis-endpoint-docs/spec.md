## ADDED Requirements

### Requirement: Driver pace profile endpoint documentation
Each analysis and fantasy route file SHALL include a `_DESCRIPTION` string, a `_RESPONSES` dict, and a `summary=` string on the `@router.get` decorator, following the pattern established in `routes/v1/meetings.py`.

The `_DESCRIPTION` for `GET /v1/analysis/driver-pace-profile` SHALL explain:
- The endpoint returns a multi-dimensional qualifying and race pace profile for a single driver across recent race weekends
- `qpace_score` (0–100) reflects weighted qualifying position — higher is better, recent sessions weighted more heavily
- `qpace_trend` indicates whether qualifying pace is improving, stable, or declining over the sample
- `sector_N_delta` is the driver's average gap to the fastest sector time in the field (seconds; lower is better)
- `rpace_score` is a normalized race pace derived from clean-air prime-window laps only (null if insufficient data)
- `rpace_percentile` ranks the driver's race pace against all other drivers in the same sessions
- `overtake_adjustment` captures average net positions gained per race from grid positions P10 and lower

#### Scenario: Driver pace profile has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/driver-pace-profile` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: DNF rates endpoint documentation
The `_DESCRIPTION` for `GET /v1/analysis/dnf-rates` SHALL explain:
- Returns per-driver DNF, DNS, and DSQ counts and rates across competitive sessions (Qualifying, Race, Sprint)
- `reliability_score` (0–100) is the inverse of the combined failure rate — 100 means no retirements in the sample
- `breakdown` gives failure rates split by session type, useful for isolating mechanical vs incident-driven retirements
- Only sessions where the driver has a result entry are counted (absent drivers are not penalised)

#### Scenario: DNF rates has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/dnf-rates` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: Fastest lap candidates endpoint documentation
The `_DESCRIPTION` for `GET /v1/analysis/fastest-lap-candidates` SHALL explain:
- Returns per-driver fastest lap statistics across Race and Sprint sessions, useful for F1 Fantasy fastest-lap point predictions
- `fl_rate` is the proportion of sessions where the driver set the fastest eligible lap (SC-affected laps excluded)
- `fl_on_fresh_tyre_rate` indicates how often the driver sets their fastest lap on a new tyre (tyre age ≤ 2 laps) — a sign of a deliberate late-stop strategy
- `typical_fl_position` is the driver's average finishing position in sessions where they set the fastest lap

#### Scenario: Fastest lap candidates has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/fastest-lap-candidates` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: Overtake profile endpoint documentation
The `_DESCRIPTION` for `GET /v1/analysis/overtake-profile` SHALL explain:
- Returns offensive and defensive overtake statistics per driver from Race and Sprint sessions
- `aggression_score` (0–100) is a percentile rank of the driver's overtake rate vs the full field — 100 means most overtakes made
- `circuit_overtake_avg` is populated only when a circuit filter is active, showing the driver's per-session average at that specific circuit
- Sprint weekends contribute two sessions to `total_races` (Race + Sprint counted separately)

#### Scenario: Overtake profile has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/overtake-profile` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: Circuit profile endpoint documentation
The `_DESCRIPTION` for `GET /v1/analysis/circuit-profile` SHALL explain:
- Returns circuit DNA metrics derived from historical race sessions at that circuit over the requested number of calendar years
- `overtake_difficulty` and `qualifying_importance` are derived from average overtakes per race — high difficulty circuits favour starting position
- `safety_car_tendency` is derived from the proportion of laps significantly slower than the session median (a proxy for SC/VSC periods)
- `weather_variability` reflects how often rainfall was recorded during race sessions at this circuit
- `typical_compounds` lists tyre compounds in frequency order across race stints

#### Scenario: Circuit profile has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/circuit-profile` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: Championship context endpoint documentation
The `_DESCRIPTION` for `GET /v1/analysis/championship-context` SHALL explain:
- Returns championship standings enriched with momentum, desperation, and constructor battle context for each driver and constructor
- `momentum` compares a driver's points in their last 3 races to their season average — POSITIVE means recent form is outpacing their trend
- `desperation_index` (0–100) measures how far behind a driver is relative to the points still available — 100 means mathematically eliminated
- `constructor_battle` flags drivers whose constructor is within 30 points of an adjacent constructor position

#### Scenario: Championship context has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/championship-context` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: Qualifying trends endpoint documentation
The `_DESCRIPTION` for `GET /v1/analysis/qualifying-trends` SHALL explain:
- Returns sector dominance, Q2/Q3 appearance rates, and qualifying performance trend for a single driver
- `q3_appearance_rate` uses grid position as a proxy — positions 1–10 indicate Q3 qualification
- `sector_dominance` shows per-sector average gap to the field fastest and the proportion of sessions where this driver set the fastest sector time
- `grid_vs_expected` is the average difference between actual grid position and championship standing — negative means regularly qualifying better than their points position suggests
- `recent_trend` compares the first and second halves of the sample window to detect whether form is improving or declining

#### Scenario: Qualifying trends has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/qualifying-trends` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: Constructor pitstop endpoint documentation
The `_DESCRIPTION` for `GET /v1/analysis/constructor-pitstop` SHALL explain:
- Returns pit stop speed distribution and F1 Fantasy scoring yield per constructor across Race and Sprint sessions
- `fantasy_points_avg` is the average F1 Fantasy points per race from pit stop scoring brackets (<2.0s = 20pts, 2.0–2.19s = 10pts, etc.) plus a +5 bonus for the session's fastest stop
- `consistency_score` (0–100) is derived from the standard deviation of stop durations — 100 means perfectly consistent, lower means high variance
- `sub_2s_rate` is the proportion of stops completed in under 2 seconds — the threshold for maximum F1 Fantasy bracket points
- Stops with null duration or over 60 seconds are excluded as non-standard

#### Scenario: Constructor pitstop has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/analysis/constructor-pitstop` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

### Requirement: Fantasy prices endpoint documentation
The `_DESCRIPTION` for `GET /v1/fantasy/prices` SHALL explain:
- Returns the static 2025 F1 Fantasy driver and constructor price list — no authentication required
- Prices are manually maintained and reflect the official F1 Fantasy values; `last_updated` indicates when they were last revised
- All prices are in millions (e.g. `28.5` = $28.5M) and are guaranteed to fall within the official F1 Fantasy range of $3M–$34M

#### Scenario: Fantasy prices has description and examples in OpenAPI
- **WHEN** `GET /openapi.json` is fetched
- **THEN** the `/v1/fantasy/prices` path object includes a non-empty `description`, a `summary`, and a `200` response with an `example` payload

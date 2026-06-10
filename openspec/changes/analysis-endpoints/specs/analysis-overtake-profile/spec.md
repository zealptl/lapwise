## ADDED Requirements

### Requirement: Overtake profile endpoint
The system SHALL expose `GET /v1/analysis/overtake-profile` returning offensive and defensive overtake statistics per driver from Race and Sprint sessions.

**Query parameters:**
- `driver_number` (int, optional): if provided, returns only this driver; if omitted returns all drivers
- `last_n_races` (int, optional, default 12): number of race weekends to include
- `session_key` (int, optional): constrains to meetings at the same circuit as this session
- `include_circuit_history` (bool, optional, default false): merges same circuit meetings from previous 2 calendar years

**Sessions used:** Race and Sprint only (`session_type IN ("Race", "Sprint")`).

**Response fields (per driver):**
- `driver_number` (int)
- `overtakes_made` (int): total overtakes made (`overtaking_driver_number = this driver`) across sample
- `overtakes_lost` (int): total times this driver was overtaken (`overtaken_driver_number = this driver`)
- `net_overtakes` (int): `overtakes_made - overtakes_lost`
- `overtake_rate` (float): `overtakes_made / total_races` — average overtakes made per race weekend
- `defensive_rate` (float): `overtakes_lost / total_races`
- `aggression_score` (float): percentile rank of `overtake_rate` vs all drivers in the same sample, normalized 0–100 (100 = most overtakes made)
- `circuit_overtake_avg` (float | null): avg overtakes made per session at the specific circuit — only populated when `session_key` or `include_circuit_history` is provided; null otherwise
- `sample_races` (int): number of race weekends included
- `total_races` (int): total Race + Sprint sessions counted (sprint weekends contribute 2 sessions)

**Calculation:**
1. Fetch last N meeting_keys via common utility
2. Fetch Race + Sprint sessions for those meetings
3. For each session_key, fetch all overtake records
4. Count `overtaking_driver_number` and `overtaken_driver_number` per driver
5. `total_races = count of sessions` (not meetings — each session counted separately for rate)
6. `aggression_score`: rank this driver's `overtake_rate` among all drivers, express as percentile

#### Scenario: All drivers overtake profile
- **WHEN** `GET /v1/analysis/overtake-profile?last_n_races=12`
- **THEN** returns overtake stats for all drivers across last 12 race weekends' race and sprint sessions

#### Scenario: Single driver with circuit filter
- **WHEN** `GET /v1/analysis/overtake-profile?driver_number=4&session_key=9165&include_circuit_history=true`
- **THEN** returns overtake profile for driver 4 at that circuit including previous 2 years, with `circuit_overtake_avg` populated

#### Scenario: Driver with zero overtakes
- **WHEN** a driver made no overtakes in the sample
- **THEN** `overtakes_made=0`, `overtake_rate=0.0`, `aggression_score=0.0`

#### Scenario: Sprint weekend session count
- **WHEN** a race weekend includes both a Sprint and a Race session
- **THEN** both sessions are counted separately in `total_races` (contributing 2 to the denominator)

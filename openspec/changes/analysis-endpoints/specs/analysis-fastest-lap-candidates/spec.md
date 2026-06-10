## ADDED Requirements

### Requirement: Fastest lap candidates endpoint
The system SHALL expose `GET /v1/analysis/fastest-lap-candidates` returning fastest lap probability per driver based on historical race and sprint sessions.

**Query parameters:**
- `last_n_races` (int, optional, default 12): number of race weekends to include
- `session_key` (int, optional): constrains to meetings at the same circuit as this session
- `include_circuit_history` (bool, optional, default false): merges same circuit meetings from previous 2 calendar years

**Fastest lap eligibility:** only Race and Sprint sessions. A lap is eligible for fastest lap credit if:
- `is_pit_out_lap = False`
- `lap_duration` is not null
- `lap_duration <= 1.10 * session_median_lap_duration` (SC exclusion)

**Response fields (per driver):**
- `driver_number` (int)
- `fastest_lap_count` (int): number of sessions where this driver set the fastest eligible lap
- `total_sessions` (int): total race + sprint sessions in the sample
- `fl_rate` (float): `fastest_lap_count / total_sessions` (0.0–1.0)
- `typical_fl_position` (float | null): avg finishing position (from `session_result.position`) in sessions where this driver set the fastest lap; null if no FL recorded
- `fl_on_fresh_tyre_rate` (float | null): proportion of FL sessions where the FL lap had `tyre_age <= 2` (fresh tyre stop tactic); null if no FL recorded
- `sample_races` (int): number of race weekends included

**Calculation:**
1. Fetch last N meeting_keys via common utility
2. Fetch Race + Sprint sessions for those meetings
3. For each session, fetch all laps across all drivers
4. Apply eligibility filters (no pit-out, non-null duration, ≤110% median)
5. Find the single lap with `min(lap_duration)` in that session → credit that driver
6. Join with stints to compute `tyre_age = lap_number - stint.lap_start + stint.tyre_age_at_start` for the FL lap
7. `fl_on_fresh_tyre_rate = count(tyre_age <= 2) / fastest_lap_count`
8. Join with `session_result.position` for `typical_fl_position`

#### Scenario: Standard fastest lap candidates request
- **WHEN** `GET /v1/analysis/fastest-lap-candidates?last_n_races=12`
- **THEN** returns all drivers ranked by fl_rate across last 12 race weekends' race and sprint sessions

#### Scenario: Fastest lap on fresh tyre
- **WHEN** a driver sets the fastest lap on a lap where tyre_age is 1
- **THEN** that session is counted in `fl_on_fresh_tyre_rate` numerator

#### Scenario: SC period fastest lap excluded
- **WHEN** all eligible laps exceed 110% of session median (e.g. heavily disrupted race)
- **THEN** no fastest lap credit is assigned for that session

#### Scenario: Tied fastest laps
- **WHEN** two drivers have identical `lap_duration` for the session minimum
- **THEN** both receive fastest lap credit for that session (both `fastest_lap_count` incremented)

#### Scenario: Circuit-specific request
- **WHEN** `GET /v1/analysis/fastest-lap-candidates?session_key=9165&include_circuit_history=true`
- **THEN** merges current-season meetings at that circuit with previous 2 years of the same circuit

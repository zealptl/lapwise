## ADDED Requirements

### Requirement: Driver pace profile endpoint
The system SHALL expose `GET /v1/analysis/driver-pace-profile` returning qualification pace (Qpace) and race pace (Rpace) metrics for a driver.

**Query parameters:**
- `driver_number` (int, required): car number of the driver
- `last_n_races` (int, optional, default 12): number of race weekends to include
- `session_key` (int, optional): if provided, constrains to meetings at the same circuit as this session
- `include_circuit_history` (bool, optional, default false): when true, merges meetings from the same circuit in the previous 2 calendar years

**Response fields:**
- `driver_number` (int)
- `qpace_score` (float): weighted average qualifying position score (1st=20, 2nd=19 … 20th=1), decay factor 0.85 per race back, normalized 0–100
- `qpace_trend` (str): `"IMPROVING"` | `"STABLE"` | `"DECLINING"` — compare weighted avg of first half vs second half of sample; threshold ±10%
- `sector_1_delta` (float | null): avg gap to fastest S1 time across sample qualifying sessions (seconds; lower is better)
- `sector_2_delta` (float | null): avg gap to fastest S2 time (seconds)
- `sector_3_delta` (float | null): avg gap to fastest S3 time (seconds)
- `strongest_sector` (str | null): `"S1"` | `"S2"` | `"S3"` — sector with smallest average delta
- `rpace_score` (float | null): median normalized clean-air lap time across sample race sessions (normalized by dividing by session median, lower is better; null if insufficient clean laps)
- `rpace_percentile` (float | null): driver's rpace_score percentile vs all drivers in same sessions (0=slowest, 100=fastest)
- `overtake_adjustment` (float): avg net positions gained per race from P10+ starting positions; positive = recovers well, negative = struggles in traffic
- `sample_races` (int): number of meetings included

**Qpace calculation:**
1. Fetch last N meeting_keys via common utility
2. Fetch qualifying sessions for those meetings
3. For each session, get `starting_grid` entry for this driver — use `position` field
4. Convert position to score: `score = 21 - position` (P1=20, P20=1; NC/no entry = 0)
5. Apply exponential decay: `weight_i = 0.85 ^ i` where i=0 is most recent
6. `qpace_score = sum(score_i * weight_i) / sum(weight_i) * 5` (normalized to 0–100)

**Rpace calculation:**
1. Fetch race sessions for those meetings
2. For each session, fetch all laps for this driver
3. Filter laps: `is_pit_out_lap=False`, `lap_number > 1`, `lap_duration` not null
4. Exclude laps where `lap_duration > 1.10 * session_median_lap_duration`
5. Join with stints: compute `tyre_age = lap_number - stint.lap_start + stint.tyre_age_at_start`
6. Keep only laps where `3 <= tyre_age <= 15`
7. `normalized_time = lap_duration / session_median_lap_duration`
8. `rpace_score = median(normalized_times)` across all qualifying laps in sample

**Sector delta calculation:**
1. Fetch laps for qualifying sessions only
2. For each session, find `min(duration_sector_X)` across ALL drivers (fastest in field)
3. Find this driver's best `duration_sector_X` in the same session
4. `delta = driver_best - session_fastest` (always >= 0)
5. `sector_X_delta = mean(deltas)` across sessions where both values are non-null

#### Scenario: Standard pace profile request
- **WHEN** `GET /v1/analysis/driver-pace-profile?driver_number=1&last_n_races=12`
- **THEN** returns qpace_score, rpace_score, sector deltas, and trend for driver 1 based on last 12 race weekends

#### Scenario: Circuit-specific request with history
- **WHEN** `GET /v1/analysis/driver-pace-profile?driver_number=16&session_key=9165&include_circuit_history=true`
- **THEN** merges current-season meetings at that circuit with the same circuit's meetings from the previous 2 years

#### Scenario: Insufficient clean laps for Rpace
- **WHEN** the driver has fewer than 3 clean-air laps in the prime tyre window across the sample
- **THEN** `rpace_score` and `rpace_percentile` are null; `sample_races` reflects the actual count

#### Scenario: Driver not in qualifying session
- **WHEN** the driver has no `starting_grid` entry for a qualifying session in the sample
- **THEN** that session contributes 0 to the qpace score (treated as NC)

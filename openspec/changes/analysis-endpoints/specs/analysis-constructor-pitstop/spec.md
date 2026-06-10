## ADDED Requirements

### Requirement: Constructor pitstop analysis endpoint
The system SHALL expose `GET /v1/analysis/constructor-pitstop` returning pit stop speed distribution and F1 Fantasy scoring yield per constructor.

**Query parameters:**
- `team_name` (str, optional): if provided, returns only this constructor; if omitted returns all constructors
- `last_n_races` (int, optional, default 12): number of race weekends to include
- `include_circuit_history` (bool, optional, default false): merges same circuit meetings from previous 2 calendar years

**Sessions used:** Race and Sprint only (`session_type IN ("Race", "Sprint")`).

**Pit stop field used:** `stop_duration` (stationary stop time — what F1 Fantasy scores). `lane_duration` is also returned for completeness but is not used in scoring calculations.

**Response fields (per constructor):**
- `team_name` (str)
- `avg_stop_duration` (float | null): mean `stop_duration` across all stops in sample (seconds); null if no valid stops
- `avg_lane_duration` (float | null): mean `lane_duration` across all stops in sample (seconds)
- `fastest_stop_in_sample` (float | null): single fastest `stop_duration` recorded across entire sample
- `fantasy_points_avg` (float): average F1 Fantasy points per race from pitstop scoring, computed as:
  - Per stop: apply bracket to `stop_duration`: >3.0s=0, 2.5–2.99s=2, 2.2–2.49s=5, 2.0–2.19s=10, <2.0s=20
  - Per race session: sum bracket points for all this constructor's stops + 5 if they had the fastest stop in the field that session
  - Average across all race sessions in sample
- `fastest_pitstop_rate` (float): proportion of race sessions where this constructor had the single fastest stop in the field (ties: both constructors get credit)
- `sub_2s_rate` (float): proportion of all stops in sample where `stop_duration < 2.0`
- `consistency_score` (float): `max(0, 100 - (std_dev_stop_duration * 100))` — lower std deviation = higher score; 100 = perfectly consistent
- `sample_stops` (int): total pit stops included in calculations
- `sample_races` (int): number of race weekends included

**Constructor assignment:**
Pit stop records contain `driver_number`. Driver-to-constructor mapping is resolved via the `drivers` endpoint filtered to the same session. Each stop is attributed to the constructor of the driver who made the stop.

**Filtering:**
- Exclude stops where `stop_duration` is null
- Exclude stops where `stop_duration > 60` (outlier — driver was stationary for a non-standard reason, e.g. recovery, mechanic incident)

#### Scenario: All constructors request
- **WHEN** `GET /v1/analysis/constructor-pitstop?last_n_races=12`
- **THEN** returns pitstop analytics for all constructors across last 12 race weekends' race and sprint sessions

#### Scenario: Fantasy points calculation with fastest pitstop
- **WHEN** a constructor has avg stop_duration of 2.35s and wins fastest pitstop in 50% of races
- **THEN** `fantasy_points_avg = 5 (bracket) + 0.5 * 5 (fastest bonus) = 7.5`

#### Scenario: Sub-2-second stop
- **WHEN** a constructor records a stop_duration of 1.95s
- **THEN** that stop contributes 20 to the bracket score and is counted in `sub_2s_rate`

#### Scenario: Tied fastest pitstop
- **WHEN** two constructors both record the minimum stop_duration in a race session
- **THEN** both receive `fastest_pitstop_rate` credit for that session

#### Scenario: Null stop_duration excluded
- **WHEN** a pit stop record has `stop_duration=null`
- **THEN** it is excluded from all calculations including sample_stops count

#### Scenario: Outlier stop excluded
- **WHEN** a stop_duration exceeds 60 seconds
- **THEN** it is excluded from calculations (non-standard stop)

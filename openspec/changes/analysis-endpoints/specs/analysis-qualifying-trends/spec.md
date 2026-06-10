## ADDED Requirements

### Requirement: Qualifying trends endpoint
The system SHALL expose `GET /v1/analysis/qualifying-trends` returning sector dominance, Q2/Q3 appearance rates, and qualifying performance trends per driver.

**Query parameters:**
- `driver_number` (int, required): car number of the driver
- `last_n_races` (int, optional, default 12): number of race weekends to include
- `include_circuit_history` (bool, optional, default false): merges same circuit meetings from previous 2 calendar years

**Sessions used:** Qualifying sessions only (`session_type = "Qualifying"`).

**Response fields:**
- `driver_number` (int)
- `avg_grid_position` (float): exponentially decay-weighted average grid position (most recent = heavier; decay factor 0.85)
- `best_grid_position` (int): best (lowest number) qualifying result in sample
- `worst_grid_position` (int): worst (highest number) qualifying result in sample (excluding NC/no-time)
- `q2_appearance_rate` (float): proportion of qualifying sessions where driver finished in positions 1–15 (proxy for Q2 qualification)
- `q3_appearance_rate` (float): proportion of qualifying sessions where driver finished in positions 1–10 (proxy for Q3 qualification)
- `sector_dominance` (object):
  - `sector_1` (object):
    - `avg_delta_to_fastest` (float | null): avg gap to fastest S1 across sample qualifying sessions (seconds)
    - `dominance_rate` (float): proportion of sessions where this driver set the fastest S1 time in the field
  - `sector_2` (object): same structure
  - `sector_3` (object): same structure
- `strongest_sector` (str | null): `"S1"` | `"S2"` | `"S3"` — sector with smallest `avg_delta_to_fastest`; null if sector data unavailable
- `grid_vs_expected` (float): avg difference between actual grid position and championship position at time of qualifying; negative = overperforming in quali vs championship standing
- `recent_trend` (str): `"IMPROVING"` | `"STABLE"` | `"DECLINING"` — compare decay-weighted avg of first half vs second half of sample; threshold ±10%
- `sample_races` (int): number of qualifying sessions included

**Q2/Q3 appearance proxy:**
OpenF1 does not expose which session (Q1/Q2/Q3) a lap was set in. Grid position from `starting_grid` is used as a proxy:
- Positions 1–10 → reached Q3
- Positions 1–15 → reached Q2
This is directionally accurate for all normal qualifying sessions.

**Sector dominance calculation:**
1. For each qualifying session, fetch all laps for all drivers (session_type = "Qualifying")
2. Find `min(duration_sector_X)` across all drivers — that driver set the fastest sector
3. `dominance_rate = sessions where this driver had min sector time / total sessions with sector data`
4. `avg_delta_to_fastest`: for each session, `driver_best_sector - session_min_sector`; average across sessions where both are non-null

**grid_vs_expected calculation:**
1. For each qualifying session, get this driver's grid position from `starting_grid`
2. Get this driver's championship position at the time (from `championship_drivers.position_start` for the same meeting_key)
3. `delta = grid_position - championship_position` (negative = qualified better than standing)
4. Average across all sessions

#### Scenario: Standard qualifying trends request
- **WHEN** `GET /v1/analysis/qualifying-trends?driver_number=16&last_n_races=12`
- **THEN** returns full qualifying profile for driver 16 across last 12 race weekends

#### Scenario: Q3 appearance rate calculation
- **WHEN** a driver finished in positions 1–10 in 8 of 12 qualifying sessions
- **THEN** `q3_appearance_rate = 0.667`

#### Scenario: Sector dominance leader
- **WHEN** a driver set the fastest S1 time in 7 of 12 sessions
- **THEN** `sector_1.dominance_rate = 0.583`

#### Scenario: Overperforming in qualifying
- **WHEN** a driver qualifies P3 consistently but sits P7 in the championship
- **THEN** `grid_vs_expected` is negative (e.g. -4.0)

#### Scenario: Missing sector data
- **WHEN** `duration_sector_1` is null for most laps in a session
- **THEN** `sector_1.avg_delta_to_fastest` is null for that session and excluded from the average

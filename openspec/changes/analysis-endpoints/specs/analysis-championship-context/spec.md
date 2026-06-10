## ADDED Requirements

### Requirement: Championship context endpoint
The system SHALL expose `GET /v1/analysis/championship-context` returning momentum, desperation index, and constructor battle flags per driver and constructor.

**Query parameters:**
- `season` (int, optional, default current season): championship year
- `after_round` (int, optional): if provided, returns standings after this meeting_key; if omitted uses latest available data

**Response fields — drivers (list):**
- `driver_number` (int)
- `team_name` (str | null)
- `points_current` (float): championship points after latest included meeting
- `championship_position` (int): current standing
- `points_gap_to_leader` (float): gap to P1 in points (0 for leader)
- `points_gap_to_p3` (float): gap to P3 (0 if in top 3; negative if ahead of P3)
- `momentum` (str): `"POSITIVE"` | `"NEUTRAL"` | `"NEGATIVE"` — based on points scored in last 3 races vs season average
- `desperation_index` (float): 0–100; higher = further behind with less time to recover
- `constructor_battle` (bool): whether this driver's constructor is within 30 points of an adjacent constructor position

**Response fields — constructors (list):**
- `team_name` (str)
- `points_current` (float)
- `constructor_position` (int)
- `points_gap_to_next` (float): points gap to the constructor immediately ahead (0 for P1)
- `under_pressure` (bool): within 30 points of the constructor immediately above or below

**Momentum calculation:**
1. Fetch championship_drivers records for last 3 race meetings
2. Points scored per meeting = `points_current - points_start` for each `championship_drivers` record
3. `last_3_avg = mean(points scored in last 3 meetings)`
4. `season_avg = total points / total meetings raced`
5. POSITIVE if `last_3_avg > season_avg * 1.20`; NEGATIVE if `last_3_avg < season_avg * 0.80`; else NEUTRAL

**Desperation index calculation:**
1. `max_remaining_points = remaining_races * 26` (25 for win + 1 for FL, approximate)
2. `gap = points_gap_to_leader`
3. If `gap > max_remaining_points`: `desperation_index = 100` (mathematically eliminated)
4. Else: `desperation_index = (gap / max_remaining_points) * 100`

#### Scenario: Championship leader
- **WHEN** a driver is in P1 in the championship
- **THEN** `points_gap_to_leader=0.0`, `desperation_index=0.0`

#### Scenario: Positive momentum
- **WHEN** a driver scored 45 points in last 3 races and their season avg is 15 per race
- **THEN** `momentum="POSITIVE"` (45/3=15 avg, but last_3_avg=15 = season_avg, so actually NEUTRAL — example: last 3 avg = 25, season avg = 15 → POSITIVE)

#### Scenario: Constructor under pressure
- **WHEN** two constructors are separated by 25 points
- **THEN** both have `under_pressure=True`

#### Scenario: After round filter
- **WHEN** `after_round=1242` is provided
- **THEN** standings reflect the state after meeting_key 1242, not the most recent meeting

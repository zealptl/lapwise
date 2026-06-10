## ADDED Requirements

### Requirement: Shared meeting resolution utility
The system SHALL provide a shared async function `get_last_n_meeting_keys(client, n, year, circuit_key, year_range)` in `services/analysis/common.py` that returns a deduplicated list of `meeting_key` integers.

- When `year` is provided, only meetings from that season are considered.
- When `circuit_key` and `year_range=(start, end)` are provided, all meetings at that circuit within the year range are included and merged with any other results, deduplicated by `meeting_key`.
- Results are sorted by `date_start` descending before slicing to `n`. Circuit history meetings are merged before slicing — the slice applies to the combined set.
- When `circuit_key` and `year_range` are provided without a base `n` limit, all matching circuit meetings are returned (caller passes `n=9999`).

#### Scenario: Last N meetings current season
- **WHEN** called with `n=12` and no circuit filter
- **THEN** returns the 12 most recent `meeting_key` values ordered by `date_start` descending

#### Scenario: Circuit history merge
- **WHEN** called with `n=9999`, `circuit_key=6`, `year_range=(2023, 2024)`
- **THEN** returns all meeting_keys for circuit 6 in 2023 and 2024

#### Scenario: Deduplication when circuit overlaps current season
- **WHEN** a circuit_key meeting falls within both the current season and the year_range
- **THEN** the meeting_key appears only once in the result

### Requirement: Shared session resolution utility
The system SHALL provide a shared async function `get_sessions_for_meetings(client, meeting_keys, session_types)` in `services/analysis/common.py` that returns all `Session` objects matching the given session_types across the provided meeting_keys.

- `session_types` is a list of strings matching `Session.session_type` values (e.g. `["Race", "Qualifying", "Sprint"]`).
- Sessions are fetched in parallel using `asyncio.gather()` — one call per meeting_key.
- Cancelled sessions (`is_cancelled=True`) are excluded from results.

#### Scenario: Race and sprint sessions only
- **WHEN** called with `session_types=["Race", "Sprint"]` for 12 meeting_keys
- **THEN** returns only sessions where `session_type` is "Race" or "Sprint", excluding cancelled sessions

#### Scenario: Parallel fetch
- **WHEN** called with a list of 12 meeting_keys
- **THEN** all session fetches are issued concurrently via asyncio.gather, not sequentially

#### Scenario: Cancelled session exclusion
- **WHEN** a session has `is_cancelled=True`
- **THEN** it is excluded from the returned list regardless of session_type match

### Requirement: Safety car lap exclusion threshold
The system SHALL define a shared constant `SC_LAP_EXCLUSION_THRESHOLD = 1.10` used by analysis services to exclude laps where `lap_duration > threshold * session_median_lap_duration`.

#### Scenario: Slow lap excluded
- **WHEN** a lap's duration is more than 110% of the session median
- **THEN** it is excluded from pace and fastest-lap calculations

#### Scenario: Normal lap included
- **WHEN** a lap's duration is within 110% of the session median
- **THEN** it is eligible for inclusion in calculations (subject to other filters)

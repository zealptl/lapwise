## ADDED Requirements

### Requirement: Circuit profile endpoint
The system SHALL expose `GET /v1/analysis/circuit-profile` returning circuit DNA metrics derived from historical race data.

**Query parameters:**
- `circuit_key` (int, required): OpenF1 circuit identifier
- `last_n_years` (int, optional, default 3): number of calendar years of data to include (e.g. 3 = current year + 2 previous)

**Response fields:**
- `circuit_key` (int)
- `circuit_short_name` (str | null): from sessions data
- `overtake_difficulty` (str): `"LOW"` | `"MEDIUM"` | `"HIGH"` — derived from avg overtakes per race session: HIGH if avg < 15, MEDIUM if 15–30, LOW if > 30
- `qualifying_importance` (float): 0–100 score; `100 - (overtake_difficulty_normalized * 100)` where HIGH difficulty → 100 (qualifying critical), LOW → 33
- `avg_overtakes_per_race` (float): raw average overtakes per race session in sample
- `safety_car_tendency` (str): `"LOW"` | `"MEDIUM"` | `"HIGH"` — derived from proportion of laps per race session where `lap_duration > 1.10 * session_median`: HIGH if > 15%, MEDIUM if 5–15%, LOW if < 5%
- `typical_compounds` (list[str]): tyre compounds used in race sessions sorted by frequency descending (e.g. `["MEDIUM", "HARD", "SOFT"]`)
- `weather_variability` (str): `"LOW"` | `"MEDIUM"` | `"HIGH"` — derived from variance in `rainfall` boolean across weather records for race sessions; HIGH if > 30% of records show rainfall
- `fl_typical_lap` (float | null): avg lap number when fastest lap was set across race sessions in sample; null if insufficient data
- `avg_pit_stops` (float): avg number of pit stops per driver per race session (`avg(stint_count - 1)` per driver per session)
- `sample_years` (int): number of calendar years included

**Calculation:**
1. Fetch all meetings at `circuit_key` for the last `last_n_years` calendar years
2. Fetch Race sessions for those meetings
3. **Overtake difficulty**: fetch overtakes per race session, compute avg; apply threshold
4. **Safety car tendency**: for each race session, compute `pct_laps_above_threshold = count(lap_duration > 1.10 * median) / total_laps`; average across sessions; apply threshold
5. **Typical compounds**: fetch stints for race sessions, count compound frequencies, sort descending
6. **Weather variability**: fetch weather records for race sessions, compute `pct_rainfall = count(rainfall=True) / total_records`; HIGH > 30%, MEDIUM 10–30%, LOW < 10%
7. **FL typical lap**: for each race session find the lap_number of the min eligible lap_duration; average across sessions
8. **Avg pit stops**: for each driver per session, count stints; subtract 1 (first stint doesn't require a stop); average across all drivers and sessions

#### Scenario: Low overtake circuit
- **WHEN** circuit has avg < 15 overtakes per race across sample
- **THEN** `overtake_difficulty="HIGH"`, `qualifying_importance` is close to 100

#### Scenario: High rainfall circuit
- **WHEN** > 30% of weather records show rainfall across race sessions
- **THEN** `weather_variability="HIGH"`

#### Scenario: Compound frequency ordering
- **WHEN** MEDIUM was used in 80% of stints and HARD in 20%
- **THEN** `typical_compounds=["MEDIUM", "HARD"]`

#### Scenario: Insufficient data
- **WHEN** fewer than 2 race sessions exist in the sample for this circuit
- **THEN** fields derived from insufficient data are null; `sample_years` reflects actual data available

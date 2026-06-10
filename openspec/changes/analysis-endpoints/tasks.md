## 1. Shared Analysis Utility

- [x] 1.1 Create `service/src/lapwise/services/analysis/__init__.py`
- [x] 1.2 Implement `get_last_n_meeting_keys(client, n, year, circuit_key, year_range)` in `service/src/lapwise/services/analysis/common.py` — fetches meetings, sorts by date descending, slices to N, supports circuit_key + year_range merge with deduplication
- [x] 1.3 Implement `get_sessions_for_meetings(client, meeting_keys, session_types)` in `common.py` — parallel fetch via asyncio.gather, excludes is_cancelled=True sessions
- [x] 1.4 Define `SC_LAP_EXCLUSION_THRESHOLD = 1.10` constant in `common.py`
- [x] 1.5 Write unit tests for `get_last_n_meeting_keys` covering: basic N slice, circuit_key filter, year_range merge, deduplication
- [x] 1.6 Write unit tests for `get_sessions_for_meetings` covering: session_type filter, cancelled session exclusion, parallel fetch

## 2. Pydantic Response Models

- [x] 2.1 Create `service/src/lapwise/models/analysis/__init__.py`
- [x] 2.2 Add `DriverPaceProfile` model in `service/src/lapwise/models/analysis/driver_pace.py` — all fields from spec including nested sector_dominance structure
- [x] 2.3 Add `DnfRates` and `DnfBreakdown` models in `service/src/lapwise/models/analysis/dnf_rates.py`
- [x] 2.4 Add `FastestLapCandidate` model in `service/src/lapwise/models/analysis/fastest_lap.py`
- [x] 2.5 Add `OvertakeProfile` model in `service/src/lapwise/models/analysis/overtake_profile.py`
- [x] 2.6 Add `CircuitProfile` model in `service/src/lapwise/models/analysis/circuit_profile.py`
- [x] 2.7 Add `ChampionshipContext`, `DriverChampionshipContext`, `ConstructorChampionshipContext` models in `service/src/lapwise/models/analysis/championship_context.py`
- [x] 2.8 Add `QualifyingTrends` and `SectorDominance` models in `service/src/lapwise/models/analysis/qualifying_trends.py`
- [x] 2.9 Add `ConstructorPitstop` model in `service/src/lapwise/models/analysis/constructor_pitstop.py`
- [x] 2.10 Add `FantasyPrices`, `DriverPrice`, `ConstructorPrice` models in `service/src/lapwise/models/fantasy_prices.py`

## 3. Driver Pace Profile Service + Route

- [ ] 3.1 Implement `service/src/lapwise/services/analysis/driver_pace.py` — Qpace score with exponential decay (factor 0.85), sector deltas from qualifying laps, Rpace from prime-window clean-air race laps (tyre_age 3–15, SC exclusion), rpace_percentile vs field, overtake_adjustment from P10+ starts
- [ ] 3.2 Implement qpace_trend: compare decay-weighted avg of first half vs second half, threshold ±10%
- [ ] 3.3 Create `service/src/lapwise/routes/v1/analysis/__init__.py`
- [ ] 3.4 Create `service/src/lapwise/routes/v1/analysis/driver_pace.py` — `GET /v1/analysis/driver-pace-profile` with query params: driver_number (required), last_n_races (default 12), session_key (optional), include_circuit_history (bool, default false)
- [ ] 3.5 Write unit tests for driver pace service covering: standard request, circuit history merge, insufficient clean laps (null rpace), driver absent from session (0 score contribution)

## 4. DNF Rates Service + Route

- [ ] 4.1 Implement `service/src/lapwise/services/analysis/dnf_rates.py` — competitive sessions only (Qualifying + Race + Sprint), per-driver counts, breakdown by session_type, reliability_score calculation
- [ ] 4.2 Handle driver absence: only count sessions where a session_result record exists for the driver
- [ ] 4.3 Create `service/src/lapwise/routes/v1/analysis/dnf_rates.py` — `GET /v1/analysis/dnf-rates` with query params: driver_number (optional), season (default current), last_n_races (default 12)
- [ ] 4.4 Write unit tests covering: all drivers, single driver, zero DNFs, sprint inclusion, absent driver handling

## 5. Fastest Lap Candidates Service + Route

- [ ] 5.1 Implement `service/src/lapwise/services/analysis/fastest_lap.py` — Race + Sprint sessions, SC exclusion via 110% threshold, min(lap_duration) per session across all drivers, tyre_age join for fl_on_fresh_tyre_rate, session_result join for typical_fl_position
- [ ] 5.2 Handle tied fastest laps: both drivers receive FL credit
- [ ] 5.3 Create `service/src/lapwise/routes/v1/analysis/fastest_lap.py` — `GET /v1/analysis/fastest-lap-candidates` with query params: last_n_races (default 12), session_key (optional), include_circuit_history (bool, default false)
- [ ] 5.4 Write unit tests covering: standard request, SC exclusion, tied FL, fresh tyre detection, circuit history

## 6. Overtake Profile Service + Route

- [ ] 6.1 Implement `service/src/lapwise/services/analysis/overtake_profile.py` — Race + Sprint sessions, per-driver overtakes_made and overtakes_lost, aggression_score as percentile rank vs field, circuit_overtake_avg when circuit filter active
- [ ] 6.2 Sprint weekend session count: each session (Race + Sprint) counted separately in total_races denominator
- [ ] 6.3 Create `service/src/lapwise/routes/v1/analysis/overtake_profile.py` — `GET /v1/analysis/overtake-profile` with query params: driver_number (optional), last_n_races (default 12), session_key (optional), include_circuit_history (bool, default false)
- [ ] 6.4 Write unit tests covering: all drivers, single driver, zero overtakes, sprint session counting, circuit_overtake_avg population

## 7. Circuit Profile Service + Route

- [ ] 7.1 Implement `service/src/lapwise/services/analysis/circuit_profile.py` — overtake_difficulty from avg overtakes per race (HIGH <15, MEDIUM 15–30, LOW >30), qualifying_importance derived from difficulty, safety_car_tendency from pct laps >110% median (HIGH >15%, MEDIUM 5–15%, LOW <5%), weather_variability from rainfall pct (HIGH >30%, MEDIUM 10–30%, LOW <10%), typical_compounds by frequency, fl_typical_lap avg, avg_pit_stops from stint count - 1
- [ ] 7.2 Handle insufficient data: return null for derived fields when fewer than 2 race sessions in sample
- [ ] 7.3 Create `service/src/lapwise/routes/v1/analysis/circuit_profile.py` — `GET /v1/analysis/circuit-profile` with query params: circuit_key (required), last_n_years (default 3)
- [ ] 7.4 Write unit tests covering: low overtake circuit, high rainfall, compound frequency ordering, insufficient data handling

## 8. Championship Context Service + Route

- [ ] 8.1 Implement `service/src/lapwise/services/analysis/championship_context.py` — momentum from last 3 meetings vs season avg (POSITIVE >120%, NEGATIVE <80%), desperation_index from points gap vs max_remaining (26 pts/race), constructor_battle flag (within 30 pts of adjacent position), under_pressure flag for constructors
- [ ] 8.2 Handle mathematically eliminated drivers: desperation_index = 100
- [ ] 8.3 Create `service/src/lapwise/routes/v1/analysis/championship_context.py` — `GET /v1/analysis/championship-context` with query params: season (default current), after_round (optional meeting_key)
- [ ] 8.4 Write unit tests covering: championship leader, positive momentum, constructor battle flag, after_round filter, mathematical elimination

## 9. Qualifying Trends Service + Route

- [ ] 9.1 Implement `service/src/lapwise/services/analysis/qualifying_trends.py` — Q2/Q3 appearance rates from grid position proxy (≤10 = Q3, ≤15 = Q2), sector dominance from min sector times across all drivers per session, avg_delta_to_fastest per sector, strongest_sector, grid_vs_expected from championship position delta, recent_trend with ±10% threshold
- [ ] 9.2 Handle missing sector data: exclude sessions where duration_sector_X is null for most laps
- [ ] 9.3 Create `service/src/lapwise/routes/v1/analysis/qualifying_trends.py` — `GET /v1/analysis/qualifying-trends` with query params: driver_number (required), last_n_races (default 12), include_circuit_history (bool, default false)
- [ ] 9.4 Write unit tests covering: Q3 appearance rate, sector dominance leader, overperforming in quali, missing sector data, recent trend calculation

## 10. Constructor Pitstop Service + Route

- [ ] 10.1 Implement `service/src/lapwise/services/analysis/constructor_pitstop.py` — Race + Sprint sessions, driver_number → team_name via drivers endpoint per session, stop_duration filtering (null excluded, >60s excluded), fantasy_points_avg applying scoring brackets + fastest pitstop bonus, fastest_pitstop_rate with tie handling, sub_2s_rate, consistency_score from std dev
- [ ] 10.2 Implement fantasy points bracket: >3.0s=0, 2.5–2.99s=2, 2.2–2.49s=5, 2.0–2.19s=10, <2.0s=20; +5 for fastest pitstop per session
- [ ] 10.3 Create `service/src/lapwise/routes/v1/analysis/constructor_pitstop.py` — `GET /v1/analysis/constructor-pitstop` with query params: team_name (optional), last_n_races (default 12), include_circuit_history (bool, default false)
- [ ] 10.4 Write unit tests covering: all constructors, single constructor, null stop_duration exclusion, outlier >60s exclusion, tied fastest pitstop, sub-2s scoring

## 11. Fantasy Prices Route

- [x] 11.1 Create `service/src/lapwise/routes/v1/fantasy/__init__.py`
- [x] 11.2 Create `service/src/lapwise/routes/v1/fantasy/prices.py` with hardcoded 2025 price dict — all 20 drivers and 10 constructors; include date-last-updated comment and TODO for dynamic pricing
- [x] 11.3 Register `GET /v1/fantasy/prices` route — no auth required, returns FantasyPrices model
- [x] 11.4 Write unit test: response contains 20 drivers, 10 constructors, all prices between 3.0 and 34.0

## 12. Route Registration

- [ ] 12.1 Register all analysis routes in `service/src/lapwise/routes/v1/__init__.py` under `/v1/analysis/` prefix
- [ ] 12.2 Register fantasy prices route under `/v1/fantasy/` prefix
- [ ] 12.3 Verify all new routes appear in FastAPI's auto-generated `/openapi.json`
- [ ] 12.4 Confirm existing routes are unaffected (run existing test suite)

## 13. Integration Testing

- [ ] 13.1 Test `GET /v1/analysis/driver-pace-profile?driver_number=1&last_n_races=5` against deployed API
- [ ] 13.2 Test `GET /v1/analysis/dnf-rates?last_n_races=5` returns all drivers
- [ ] 13.3 Test `GET /v1/analysis/fastest-lap-candidates?last_n_races=5`
- [ ] 13.4 Test `GET /v1/analysis/overtake-profile?last_n_races=5`
- [ ] 13.5 Test `GET /v1/analysis/circuit-profile?circuit_key=6` (Monaco)
- [ ] 13.6 Test `GET /v1/analysis/championship-context`
- [ ] 13.7 Test `GET /v1/analysis/qualifying-trends?driver_number=16`
- [ ] 13.8 Test `GET /v1/analysis/constructor-pitstop`
- [ ] 13.9 Test `GET /v1/fantasy/prices`
- [ ] 13.10 Test `include_circuit_history=true` on at least one endpoint and verify circuit history data is merged

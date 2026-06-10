## 1. Driver Pace Profile

- [x] 1.1 Add `_DESCRIPTION` to `routes/v1/analysis/driver_pace.py` explaining qpace_score, qpace_trend, sector deltas, rpace_score, rpace_percentile, and overtake_adjustment in 1–2 sentences each
- [x] 1.2 Add `_200_EXAMPLE` with a realistic payload (driver 1, plausible float values)
- [x] 1.3 Add `_RESPONSES` dict (200 with example, 422 with ErrorEnvelope, 502, 504)
- [x] 1.4 Update `@router.get` decorator with `summary=`, `description=_DESCRIPTION`, `responses=_RESPONSES`
- [x] 1.5 Expand all `Query(description=...)` strings to match wrapper endpoint verbosity

## 2. DNF Rates

- [x] 2.1 Add `_DESCRIPTION` to `routes/v1/analysis/dnf_rates.py` explaining reliability_score and breakdown fields
- [x] 2.2 Add `_200_EXAMPLE` with a realistic multi-driver payload
- [x] 2.3 Add `_RESPONSES` dict and update `@router.get` decorator with `summary=`, `description=`, `responses=`
- [x] 2.4 Expand `Query(description=...)` strings

## 3. Fastest Lap Candidates

- [x] 3.1 Add `_DESCRIPTION` to `routes/v1/analysis/fastest_lap.py` explaining fl_rate, fl_on_fresh_tyre_rate, typical_fl_position
- [x] 3.2 Add `_200_EXAMPLE` and `_RESPONSES` dict
- [x] 3.3 Update `@router.get` decorator and expand `Query` descriptions

## 4. Overtake Profile

- [x] 4.1 Add `_DESCRIPTION` to `routes/v1/analysis/overtake_profile.py` explaining aggression_score, circuit_overtake_avg, total_races denominator
- [x] 4.2 Add `_200_EXAMPLE` and `_RESPONSES` dict
- [x] 4.3 Update `@router.get` decorator with `summary=` and expand `Query` descriptions

## 5. Circuit Profile

- [x] 5.1 Add `_DESCRIPTION` to `routes/v1/analysis/circuit_profile.py` explaining overtake_difficulty, qualifying_importance, safety_car_tendency, weather_variability, typical_compounds
- [x] 5.2 Add `_200_EXAMPLE` with Monaco-like values (high difficulty, variable weather) and `_RESPONSES` dict
- [x] 5.3 Update `@router.get` decorator and expand `Query` descriptions

## 6. Championship Context

- [x] 6.1 Add `_DESCRIPTION` to `routes/v1/analysis/championship_context.py` explaining momentum, desperation_index, constructor_battle, under_pressure
- [x] 6.2 Add `_200_EXAMPLE` with realistic standings snapshot and `_RESPONSES` dict
- [x] 6.3 Update `@router.get` decorator and expand `Query` descriptions

## 7. Qualifying Trends

- [x] 7.1 Add `_DESCRIPTION` to `routes/v1/analysis/qualifying_trends.py` explaining q3_appearance_rate proxy, sector_dominance, grid_vs_expected, recent_trend
- [x] 7.2 Add `_200_EXAMPLE` and `_RESPONSES` dict
- [x] 7.3 Update `@router.get` decorator and expand `Query` descriptions

## 8. Constructor Pitstop

- [x] 8.1 Add `_DESCRIPTION` to `routes/v1/analysis/constructor_pitstop.py` explaining fantasy_points_avg brackets, consistency_score, sub_2s_rate, fastest_pitstop_rate
- [x] 8.2 Add `_200_EXAMPLE` with realistic stop durations and fantasy points and `_RESPONSES` dict
- [x] 8.3 Update `@router.get` decorator with `summary=` and expand `Query` descriptions

## 9. Fantasy Prices

- [x] 9.1 Add `_DESCRIPTION` to `routes/v1/fantasy/prices.py` explaining the static price list, last_updated field, and price range guarantee
- [x] 9.2 Add `_200_EXAMPLE` (truncated: 3 drivers, 2 constructors is sufficient) and `_RESPONSES` dict (200 + 422 only — no upstream errors for a static endpoint)
- [x] 9.3 Update `@router.get` decorator with `summary=`, `description=`, `responses=`

## 10. Verification

- [x] 10.1 Start the service locally and confirm all 9 endpoints appear in `/docs` with populated descriptions and examples
- [x] 10.2 Run existing test suite to confirm no regressions (`cd service && python -m pytest tests/unit/ -q`)

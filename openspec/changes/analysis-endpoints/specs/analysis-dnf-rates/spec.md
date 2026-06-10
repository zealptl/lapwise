## ADDED Requirements

### Requirement: DNF rates endpoint
The system SHALL expose `GET /v1/analysis/dnf-rates` returning DNF, DNS, and DSQ rates per driver across competitive sessions.

**Query parameters:**
- `driver_number` (int, optional): if provided, returns only this driver; if omitted returns all drivers
- `season` (int, optional, default current season): filter to this championship year
- `last_n_races` (int, optional, default 12): number of race weekends to include

**Competitive sessions** are defined as `session_type IN ("Qualifying", "Race", "Sprint")`. Practice sessions are excluded entirely.

**Response fields (per driver):**
- `driver_number` (int)
- `dnf_count` (int): total DNFs across all competitive sessions in sample
- `dns_count` (int): total DNSs across all competitive sessions
- `dsq_count` (int): total DSQs across all competitive sessions
- `total_sessions` (int): total competitive sessions included (denominator)
- `dnf_rate` (float): `(dnf_count + dns_count + dsq_count) / total_sessions` (0.0–1.0)
- `reliability_score` (float): `(1 - dnf_rate) * 100` (0–100; 100 = never retired)
- `breakdown` (object):
  - `qualifying_dnf_rate` (float): rate across qualifying sessions only (NC/DSQ → -5pts)
  - `race_dnf_rate` (float): rate across race sessions only (DNF → -20pts)
  - `sprint_dnf_rate` (float): rate across sprint sessions only (DNF → -10pts)
- `sample_races` (int): number of race weekends included

**Calculation:**
1. Fetch last N meeting_keys via common utility (filtered by season)
2. Fetch sessions for those meetings with `session_types=["Qualifying", "Race", "Sprint"]`
3. Fetch `session_result` for each session
4. Per driver: count `dnf=True`, `dns=True`, `dsq=True` entries
5. `total_sessions = count of session_results for this driver` (drivers who didn't participate in a session have no session_result entry — do not count that session for them)
6. Compute breakdown rates separately per session_type

#### Scenario: All drivers request
- **WHEN** `GET /v1/analysis/dnf-rates?last_n_races=12`
- **THEN** returns a list of all drivers with DNF stats across last 12 race weekends' competitive sessions

#### Scenario: Single driver request
- **WHEN** `GET /v1/analysis/dnf-rates?driver_number=44&last_n_races=8`
- **THEN** returns DNF stats for driver 44 only across last 8 race weekends

#### Scenario: Driver with no retirements
- **WHEN** a driver has zero DNF/DNS/DSQ entries in the sample
- **THEN** `dnf_rate=0.0`, `reliability_score=100.0`, all breakdown rates are 0.0

#### Scenario: Sprint session inclusion
- **WHEN** a driver DNFs in a sprint race session
- **THEN** it is counted in `dnf_count` and reflected in `sprint_dnf_rate` breakdown

#### Scenario: Driver absent from some sessions
- **WHEN** a driver has no `session_result` for a particular session (did not participate)
- **THEN** that session is not counted in `total_sessions` for that driver

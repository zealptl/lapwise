## ADDED Requirements

### Requirement: GET /v1/analysis/driver-pace-profile endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/driver-pace-profile` returning pace data for a specified driver at a specified circuit/session, including average lap time, stint-level pace breakdown, and tyre degradation indicators.

Query params: `driver_number` (required), `circuit_key` (required), `year` (required), `include_circuit_history` (optional, bool, default false).

#### Scenario: Returns pace profile for a driver
- **WHEN** `GET /v1/analysis/driver-pace-profile?driver_number=1&circuit_key=monaco&year=2025` is called
- **THEN** response SHALL contain average lap time, per-stint pace, and tyre compound data for driver 1 at Monaco 2025

#### Scenario: include_circuit_history adds prior 2 years
- **WHEN** `include_circuit_history=true` is added to the query
- **THEN** response SHALL also include pace data from the same circuit in 2024 and 2023 where available

### Requirement: GET /v1/analysis/dnf-rates endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/dnf-rates` returning historical DNF rates per driver and constructor over a specified number of recent races, with breakdown by failure type (mechanical, collision, other).

Query params: `year` (required), `circuit_key` (optional), `include_circuit_history` (optional, bool, default false), `last_n_races` (optional, int, default 5).

#### Scenario: Returns DNF rates per driver
- **WHEN** `GET /v1/analysis/dnf-rates?year=2025&last_n_races=5` is called
- **THEN** response SHALL include a DNF rate (percentage) for each driver in the last 5 races of the 2025 season

#### Scenario: Circuit-specific DNF rates with history
- **WHEN** `circuit_key=monaco&include_circuit_history=true` is included
- **THEN** response SHALL include DNF rates at Monaco for 2025, 2024, and 2023

### Requirement: GET /v1/analysis/fastest-lap-candidates endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/fastest-lap-candidates` returning a ranked list of drivers most likely to set the fastest lap, based on historical fastest lap frequency at the specified circuit and recent form.

Query params: `circuit_key` (required), `year` (required), `include_circuit_history` (optional, bool, default false).

#### Scenario: Returns ranked candidates
- **WHEN** `GET /v1/analysis/fastest-lap-candidates?circuit_key=monaco&year=2025` is called
- **THEN** response SHALL be a list of drivers sorted by historical fastest-lap frequency at Monaco, with frequency percentage

### Requirement: GET /v1/analysis/overtake-profile endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/overtake-profile` returning overtaking statistics per driver and circuit, including total overtakes made, positions gained from grid to finish, and overtake opportunity index.

Query params: `circuit_key` (required), `year` (required), `include_circuit_history` (optional, bool, default false).

#### Scenario: Returns overtake statistics per driver
- **WHEN** `GET /v1/analysis/overtake-profile?circuit_key=spa&year=2025` is called
- **THEN** response SHALL include per-driver overtake count and positions-gained at Spa for 2025

### Requirement: GET /v1/analysis/circuit-profile endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/circuit-profile` returning a circuit-level summary: overtake difficulty rating, pitstop frequency, typical tyre strategies, safety car probability, and weather tendency.

Query params: `circuit_key` (required), `year` (required), `include_circuit_history` (optional, bool, default false).

#### Scenario: Returns circuit profile
- **WHEN** `GET /v1/analysis/circuit-profile?circuit_key=monaco&year=2025` is called
- **THEN** response SHALL include overtake difficulty, pitstop frequency, tyre strategy breakdown, and safety car probability for Monaco

### Requirement: GET /v1/analysis/championship-context endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/championship-context` returning the current driver and constructor championship standings for a given season, plus each driver's points trajectory over the last N races.

Query params: `year` (required), `last_n_races` (optional, int, default 5).

#### Scenario: Returns championship standings with trajectory
- **WHEN** `GET /v1/analysis/championship-context?year=2025` is called
- **THEN** response SHALL include driver standings, constructor standings, and each driver's points in the last 5 races

### Requirement: GET /v1/analysis/qualifying-trends endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/qualifying-trends` returning qualifying performance trends per driver at a specified circuit, including historical qualifying positions and frequency of reaching Q3.

Query params: `circuit_key` (required), `year` (required), `include_circuit_history` (optional, bool, default false).

#### Scenario: Returns qualifying trends per driver
- **WHEN** `GET /v1/analysis/qualifying-trends?circuit_key=silverstone&year=2025` is called
- **THEN** response SHALL include per-driver average qualifying position and Q3 frequency at Silverstone

### Requirement: GET /v1/analysis/constructor-pitstop endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/analysis/constructor-pitstop` returning pitstop time statistics per constructor — average stop time, fastest stop, frequency of sub-2.0s stops, and frequency of stops under each F1 Fantasy scoring threshold (2.0s, 2.2s, 2.5s, 3.0s).

Query params: `circuit_key` (optional), `year` (required), `include_circuit_history` (optional, bool, default false).

#### Scenario: Returns constructor pitstop statistics
- **WHEN** `GET /v1/analysis/constructor-pitstop?year=2025` is called
- **THEN** response SHALL include per-constructor average stop time, fastest stop, and frequency breakdown by the F1 Fantasy scoring thresholds

#### Scenario: Circuit-specific pitstop data is returned when circuit_key is provided
- **WHEN** `circuit_key=monaco` is included
- **THEN** response SHALL filter pitstop data to Monaco stops only

### Requirement: All analysis endpoints require authentication
All `/v1/analysis/*` endpoints SHALL require a valid Cognito JWT in the `Authorization: Bearer` header, consistent with existing Lapwise API authorization.

#### Scenario: Unauthenticated request is rejected
- **WHEN** a request to any analysis endpoint is made without an Authorization header
- **THEN** response SHALL be HTTP 401

### Requirement: All analysis endpoints have OpenAPI documentation
Each analysis endpoint SHALL have a FastAPI `summary`, `description`, and typed response model so the `/openapi.json` spec accurately describes inputs and outputs for the AgentCore Gateway tool catalog.

#### Scenario: OpenAPI spec describes analysis endpoints
- **WHEN** `GET /openapi.json` is called
- **THEN** each `/v1/analysis/*` path SHALL appear with summary, description, and response schema

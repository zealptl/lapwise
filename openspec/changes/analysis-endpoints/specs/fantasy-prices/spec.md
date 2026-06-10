## ADDED Requirements

### Requirement: Fantasy prices endpoint
The system SHALL expose `GET /v1/fantasy/prices` returning the current 2025 F1 Fantasy driver and constructor price list as a static JSON response.

**No query parameters.**

**Response fields:**
- `season` (int): the season these prices apply to (2025)
- `last_updated` (str): ISO 8601 date string of when prices were last manually updated (e.g. `"2025-06-09"`)
- `drivers` (list): one entry per driver:
  - `driver_number` (int)
  - `full_name` (str)
  - `team_name` (str)
  - `price_millions` (float): price in millions (e.g. `28.5` = $28.5M)
- `constructors` (list): one entry per constructor:
  - `team_name` (str)
  - `price_millions` (float)

**Implementation:**
- Prices are stored as a hardcoded Python dict in `routes/v1/fantasy/prices.py`
- No database, no external fetch, no caching needed
- The file SHALL include a comment with the date last updated and a note to update after each race
- Prices are subject to the official F1 Fantasy constraints: minimum $3M, maximum $34M
- The endpoint does not require authentication — it returns public fantasy pricing data

#### Scenario: Standard prices request
- **WHEN** `GET /v1/fantasy/prices`
- **THEN** returns the full driver and constructor price list for the 2025 season with last_updated date

#### Scenario: Price range validity
- **WHEN** any driver or constructor price is returned
- **THEN** `price_millions` SHALL be between 3.0 and 34.0 inclusive

#### Scenario: All 20 drivers present
- **WHEN** the response is returned
- **THEN** `drivers` list contains exactly 20 entries covering all current F1 grid drivers

#### Scenario: All 10 constructors present
- **WHEN** the response is returned
- **THEN** `constructors` list contains exactly 10 entries covering all current F1 constructors

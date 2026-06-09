## ADDED Requirements

### Requirement: The system SHALL expose a typed `ChampionshipDriver` Pydantic model

The system SHALL define `lapwise.models.championship.ChampionshipDriver` mirroring OpenF1's `/championship_drivers` (beta) response shape.

#### Scenario: ChampionshipDriver model fields match OpenF1's documented shape
- **WHEN** `ChampionshipDriver` is introspected
- **THEN** it SHALL define at least: `driver_number: int`, `meeting_key: int`, `points_current: float`, `points_start: float`, `position_current: int`, `position_start: int`, `session_key: int`
- **AND** each field SHALL document the OpenF1 semantics (current vs. start of session)
- **AND** the model docstring SHALL note the endpoint is in beta and only available for race sessions

### Requirement: The system SHALL expose a `ChampionshipDriverService.list_standings` method

The system SHALL define `lapwise.services.championship.ChampionshipDriverService` with an async `list_standings(...)` method returning `list[ChampionshipDriver]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_standings(session_key=9839, driver_number=[4, 81])`
- **THEN** the service SHALL call the client and the upstream URL SHALL include `driver_number=4&driver_number=81`

### Requirement: The system SHALL expose `GET /v1/championship_drivers`

The system SHALL register `GET /v1/championship_drivers` returning `list[ChampionshipDriver]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/championship_drivers` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/championship_drivers` and noting beta/race-only), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts repeated `driver_number`
- **WHEN** a client calls `GET /v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81`
- **THEN** the upstream URL SHALL include `driver_number=4&driver_number=81`

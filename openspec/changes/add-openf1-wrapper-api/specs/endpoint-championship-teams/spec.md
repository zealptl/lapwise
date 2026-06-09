## ADDED Requirements

### Requirement: The system SHALL expose a typed `ChampionshipTeam` Pydantic model

The system SHALL define `lapwise.models.championship.ChampionshipTeam` mirroring OpenF1's `/championship_teams` (beta) response shape.

#### Scenario: ChampionshipTeam model fields match OpenF1's documented shape
- **WHEN** `ChampionshipTeam` is introspected
- **THEN** it SHALL define at least: `meeting_key: int`, `points_current: float`, `points_start: float`, `position_current: int`, `position_start: int`, `session_key: int`, `team_name: str`
- **AND** the model docstring SHALL note the endpoint is in beta and only available for race sessions

### Requirement: The system SHALL expose a `ChampionshipTeamService.list_standings` method

The system SHALL define `lapwise.services.championship.ChampionshipTeamService` with an async `list_standings(...)` method returning `list[ChampionshipTeam]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_standings(session_key=9839, team_name="McLaren")`
- **THEN** the service SHALL call the client and return `list[ChampionshipTeam]`

### Requirement: The system SHALL expose `GET /v1/championship_teams`

The system SHALL register `GET /v1/championship_teams` returning `list[ChampionshipTeam]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/championship_teams` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/championship_teams` and noting beta/race-only), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts `team_name` equality filter
- **WHEN** a client calls `GET /v1/championship_teams?session_key=9839&team_name=McLaren`
- **THEN** the route SHALL forward `team_name=McLaren` to the service and respond `200`

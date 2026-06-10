## ADDED Requirements

### Requirement: The system SHALL expose a typed `SessionResult` Pydantic model

The system SHALL define `lapwise.models.session_result.SessionResult` mirroring OpenF1's `/session_result` response shape. Because OpenF1 returns different shapes for race vs. qualifying, the model SHALL use Union types where needed.

#### Scenario: SessionResult model fields match OpenF1's documented shape and Union variance
- **WHEN** `SessionResult` is introspected
- **THEN** it SHALL define at least: `dnf: bool`, `dns: bool`, `dsq: bool`, `driver_number: int`, `duration: float | list[float] | None`, `gap_to_leader: float | str | None`, `number_of_laps: int | None`, `meeting_key: int`, `position: int | None`, `session_key: int`
- **AND** `duration` SHALL document that for qualifying it is an array of three values for Q1/Q2/Q3
- **AND** `gap_to_leader` SHALL document that lapped finishers appear as a string like `+1 LAP`

### Requirement: The system SHALL expose a `SessionResultService.list_results` method

The system SHALL define `lapwise.services.session_result.SessionResultService` with an async `list_results(...)` method returning `list[SessionResult]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_results(session_key=7782, position_lte=3)`
- **THEN** the service SHALL call the client with `position<=3` after translation and return `list[SessionResult]`

### Requirement: The system SHALL expose `GET /v1/session_result`

The system SHALL register `GET /v1/session_result` returning `list[SessionResult]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/session_result` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/session_result`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`
- **AND** the `200` example SHALL include a row that demonstrates the array form of `duration`

#### Scenario: Route accepts `position_lte` comparison filter
- **WHEN** a client calls `GET /v1/session_result?session_key=7782&position_lte=3`
- **THEN** the upstream URL SHALL contain `position<=3`

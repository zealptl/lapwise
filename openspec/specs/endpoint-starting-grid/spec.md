## ADDED Requirements

### Requirement: The system SHALL expose a typed `StartingGridEntry` Pydantic model

The system SHALL define `lapwise.models.starting_grid.StartingGridEntry` mirroring OpenF1's `/starting_grid` response shape.

#### Scenario: StartingGridEntry model fields match OpenF1's documented shape
- **WHEN** `StartingGridEntry` is introspected
- **THEN** it SHALL define at least: `driver_number: int`, `lap_duration: float | None`, `meeting_key: int`, `position: int`, `session_key: int`
- **AND** every field SHALL have a non-empty `description`

### Requirement: The system SHALL expose a `StartingGridService.list_grid` method

The system SHALL define `lapwise.services.starting_grid.StartingGridService` with an async `list_grid(...)` method returning `list[StartingGridEntry]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_grid(session_key=7783, position_lte=3)`
- **THEN** the service SHALL call the client with `position<=3` after translation and return `list[StartingGridEntry]`

### Requirement: The system SHALL expose `GET /v1/starting_grid`

The system SHALL register `GET /v1/starting_grid` returning `list[StartingGridEntry]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/starting_grid` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/starting_grid`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts `position_lte` comparison filter
- **WHEN** a client calls `GET /v1/starting_grid?session_key=7783&position_lte=3`
- **THEN** the upstream URL SHALL contain `position<=3`

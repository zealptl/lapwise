## ADDED Requirements

### Requirement: The system SHALL expose a typed `Position` Pydantic model

The system SHALL define `lapwise.models.position.Position` mirroring OpenF1's `/position` response shape.

#### Scenario: Position model fields match OpenF1's documented shape
- **WHEN** `Position` is introspected
- **THEN** it SHALL define at least: `date: datetime`, `driver_number: int`, `meeting_key: int`, `position: int`, `session_key: int`
- **AND** every field SHALL have a non-empty `description`

### Requirement: The system SHALL expose a `PositionService.list_positions` method

The system SHALL define `lapwise.services.position.PositionService` with an async `list_positions(...)` method returning `list[Position]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_positions(meeting_key=1217, driver_number=40, position_lte=3)`
- **THEN** the service SHALL call the client with `position<=3` after translation and return `list[Position]`

### Requirement: The system SHALL expose `GET /v1/position`

The system SHALL register `GET /v1/position` returning `list[Position]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/position` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/position`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts `position_lte` comparison filter
- **WHEN** a client calls `GET /v1/position?meeting_key=1217&driver_number=40&position_lte=3`
- **THEN** the upstream URL SHALL contain `position<=3`

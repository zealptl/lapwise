## ADDED Requirements

### Requirement: The system SHALL expose a typed `PitStop` Pydantic model

The system SHALL define `lapwise.models.pit.PitStop` mirroring OpenF1's `/pit` response shape.

#### Scenario: PitStop model fields match OpenF1's documented shape
- **WHEN** `PitStop` is introspected
- **THEN** it SHALL define at least: `date: datetime`, `driver_number: int`, `lane_duration: float | None`, `lap_number: int`, `meeting_key: int`, `pit_duration: float | None`, `session_key: int`, `stop_duration: float | None`
- **AND** `pit_duration` SHALL document that it is deprecated and equivalent to `lane_duration`

### Requirement: The system SHALL expose a `PitService.list_pit_stops` method

The system SHALL define `lapwise.services.pit.PitService` with an async `list_pit_stops(...)` method returning `list[PitStop]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_pit_stops(session_key=9877, stop_duration_lt=2.3)`
- **THEN** the service SHALL call the client with `stop_duration<2.3` after translation and return `list[PitStop]`

### Requirement: The system SHALL expose `GET /v1/pit`

The system SHALL register `GET /v1/pit` returning `list[PitStop]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/pit` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/pit`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts the `stop_duration_lt` comparison filter
- **WHEN** a client calls `GET /v1/pit?session_key=9877&stop_duration_lt=2.3`
- **THEN** the upstream URL SHALL contain `stop_duration<2.3`

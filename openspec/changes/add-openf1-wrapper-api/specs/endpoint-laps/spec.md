## ADDED Requirements

### Requirement: The system SHALL expose a typed `Lap` Pydantic model

The system SHALL define `lapwise.models.laps.Lap` mirroring OpenF1's `/laps` response shape with optional fields defaulting to `None` and per-field OpenAPI descriptions.

#### Scenario: Lap model fields match OpenF1's documented shape
- **WHEN** `Lap` is introspected
- **THEN** it SHALL define at least: `date_start: datetime | None`, `driver_number: int`, `duration_sector_1: float | None`, `duration_sector_2: float | None`, `duration_sector_3: float | None`, `i1_speed: int | None`, `i2_speed: int | None`, `is_pit_out_lap: bool | None`, `lap_duration: float | None`, `lap_number: int`, `meeting_key: int`, `segments_sector_1: list[int] | None`, `segments_sector_2: list[int] | None`, `segments_sector_3: list[int] | None`, `session_key: int`, `st_speed: int | None`
- **AND** every field SHALL have a non-empty `description`

### Requirement: The system SHALL expose a `LapService.list_laps` method

The system SHALL define `lapwise.services.laps.LapService` with an async `list_laps(...)` method that delegates to the shared `OpenF1Client` and returns `list[Lap]`.

#### Scenario: Service composes filters and returns parsed models
- **WHEN** a caller invokes `list_laps(session_key=9161, driver_number=63, lap_number=8)`
- **THEN** the service SHALL call the client with those filters and return `list[Lap]`

### Requirement: The system SHALL expose `GET /v1/laps`

The system SHALL register `GET /v1/laps` returning `list[Lap]` and supporting filters from OpenF1's docs using the hybrid syntax.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/laps` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (including a link to `https://api.openf1.org/v1/laps`), per-parameter descriptions, and example response bodies for `200`, `422`, `502`, `504`

#### Scenario: Route accepts comparison filters using `_lt`/`_lte`/`_gt`/`_gte` suffixes
- **WHEN** a client calls `GET /v1/laps?session_key=9161&lap_duration_lt=92.0`
- **THEN** the route SHALL forward `lap_duration_lt=92.0` to the service and the upstream URL SHALL contain `lap_duration<92.0`

#### Scenario: Route accepts equality and repeated-key filters mirroring OpenF1
- **WHEN** a client calls `GET /v1/laps?session_key=9161&driver_number=63&driver_number=44`
- **THEN** the upstream URL SHALL include `driver_number=63&driver_number=44`

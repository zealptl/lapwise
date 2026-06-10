## ADDED Requirements

### Requirement: The system SHALL expose a typed `Stint` Pydantic model

The system SHALL define `lapwise.models.stints.Stint` mirroring OpenF1's `/stints` response shape.

#### Scenario: Stint model fields match OpenF1's documented shape
- **WHEN** `Stint` is introspected
- **THEN** it SHALL define at least: `compound: str | None`, `driver_number: int`, `lap_end: int | None`, `lap_start: int`, `meeting_key: int`, `session_key: int`, `stint_number: int`, `tyre_age_at_start: int | None`
- **AND** `compound` SHALL document the expected values (`SOFT`, `MEDIUM`, `HARD`, `INTERMEDIATE`, `WET`, etc.)

### Requirement: The system SHALL expose a `StintService.list_stints` method

The system SHALL define `lapwise.services.stints.StintService` with an async `list_stints(...)` method returning `list[Stint]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_stints(session_key=9165, tyre_age_at_start_gte=3)`
- **THEN** the service SHALL call the client with `tyre_age_at_start>=3` after translation and return `list[Stint]`

### Requirement: The system SHALL expose `GET /v1/stints`

The system SHALL register `GET /v1/stints` returning `list[Stint]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/stints` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/stints`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts `tyre_age_at_start_gte` comparison filter
- **WHEN** a client calls `GET /v1/stints?session_key=9165&tyre_age_at_start_gte=3`
- **THEN** the upstream URL SHALL contain `tyre_age_at_start>=3`

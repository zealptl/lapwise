## ADDED Requirements

### Requirement: The system SHALL expose a typed `Meeting` Pydantic model

The system SHALL define `lapwise.models.meetings.Meeting` mirroring OpenF1's `/meetings` response shape with per-field OpenAPI descriptions.

#### Scenario: Meeting model fields match OpenF1's documented shape
- **WHEN** `Meeting` is introspected
- **THEN** it SHALL define at least: `circuit_key: int`, `circuit_info_url: str | None`, `circuit_image: str | None`, `circuit_short_name: str | None`, `circuit_type: str | None`, `country_code: str | None`, `country_flag: str | None`, `country_key: int | None`, `country_name: str | None`, `date_end: datetime | None`, `date_start: datetime | None`, `gmt_offset: str | None`, `is_cancelled: bool`, `location: str | None`, `meeting_key: int`, `meeting_name: str | None`, `meeting_official_name: str | None`, `year: int`
- **AND** every field SHALL have a non-empty `description`

### Requirement: The system SHALL expose a `MeetingService.list_meetings` method

The system SHALL define `lapwise.services.meetings.MeetingService` with an async `list_meetings(...)` method returning `list[Meeting]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_meetings(year=2026, country_name="Singapore")`
- **THEN** the service SHALL call the client and return `list[Meeting]`

### Requirement: The system SHALL expose `GET /v1/meetings`

The system SHALL register `GET /v1/meetings` returning `list[Meeting]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/meetings` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/meetings`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts the documented filters
- **WHEN** a client calls `GET /v1/meetings?year=2026&country_name=Singapore`
- **THEN** the route SHALL forward those values to the service and return `200`

#### Scenario: Route accepts `meeting_key=latest`
- **WHEN** a client calls `GET /v1/meetings?meeting_key=latest`
- **THEN** the route SHALL forward `meeting_key=latest` to the upstream unchanged
- **AND** the `meeting_key` query parameter SHALL accept either an integer or the literal string `latest`

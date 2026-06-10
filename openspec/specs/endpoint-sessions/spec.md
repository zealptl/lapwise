## ADDED Requirements

### Requirement: The system SHALL expose a typed `Session` Pydantic model

The system SHALL define `lapwise.models.sessions.Session` mirroring OpenF1's `/sessions` response shape.

#### Scenario: Session model fields match OpenF1's documented shape
- **WHEN** `Session` is introspected
- **THEN** it SHALL define at least: `circuit_key: int`, `circuit_short_name: str | None`, `country_code: str | None`, `country_key: int | None`, `country_name: str | None`, `date_end: datetime | None`, `date_start: datetime | None`, `gmt_offset: str | None`, `is_cancelled: bool`, `location: str | None`, `meeting_key: int`, `session_key: int`, `session_name: str | None`, `session_type: str | None`, `year: int`
- **AND** every field SHALL have a non-empty `description`

### Requirement: The system SHALL expose a `SessionService.list_sessions` method

The system SHALL define `lapwise.services.sessions.SessionService` with an async `list_sessions(...)` method returning `list[Session]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_sessions(country_name="Belgium", session_name="Sprint Qualifying", year=2023)`
- **THEN** the service SHALL call the client and return `list[Session]`

### Requirement: The system SHALL expose `GET /v1/sessions`

The system SHALL register `GET /v1/sessions` returning `list[Session]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/sessions` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/sessions`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts session-name filters URL-encoded
- **WHEN** a client calls `GET /v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023`
- **THEN** the route SHALL forward those values and respond `200`

#### Scenario: Route accepts `session_key=latest`
- **WHEN** a client calls `GET /v1/sessions?session_key=latest`
- **THEN** the `session_key` query parameter SHALL accept either an integer or the literal string `latest` and the value SHALL be forwarded unchanged

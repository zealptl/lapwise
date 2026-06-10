## ADDED Requirements

### Requirement: The system SHALL expose a typed `Driver` Pydantic model

The system SHALL define `lapwise.models.drivers.Driver` mirroring OpenF1's `/drivers` response shape. Optional fields SHALL default to `None`. Each field SHALL carry an OpenAPI description.

#### Scenario: Driver model fields match OpenF1's documented shape
- **WHEN** `Driver` is introspected
- **THEN** it SHALL define at least: `broadcast_name: str | None`, `country_code: str | None`, `driver_number: int`, `first_name: str | None`, `full_name: str | None`, `headshot_url: str | None`, `last_name: str | None`, `meeting_key: int`, `name_acronym: str | None`, `session_key: int`, `team_colour: str | None`, `team_name: str | None`
- **AND** every field SHALL have a non-empty `description` in its `Field(...)`

### Requirement: The system SHALL expose a `DriverService.list_drivers` method

The system SHALL define `lapwise.services.drivers.DriverService` with an async `list_drivers(...)` method that delegates filter translation and HTTP I/O to the shared `OpenF1Client` and returns `list[Driver]`.

#### Scenario: Service forwards equality and in-filters to the client
- **WHEN** a caller invokes `list_drivers(driver_number=1, session_key=9158)`
- **THEN** the service SHALL ask the client to GET `drivers` with those filters and SHALL return the parsed `list[Driver]`

#### Scenario: Service returns an empty list when OpenF1 returns no results
- **WHEN** OpenF1 returns `[]`
- **THEN** the service SHALL return `[]`

### Requirement: The system SHALL expose `GET /v1/drivers`

The system SHALL register a `GET /v1/drivers` route that returns `list[Driver]` and supports filtering by the documented OpenF1 filters using the hybrid syntax.

#### Scenario: Route is registered under the v1 router with the correct tag
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/drivers` SHALL appear under tag `OpenF1 wrappers` with a non-empty `summary` and a multi-paragraph `description` that links to `https://api.openf1.org/v1/drivers`

#### Scenario: Route accepts equality filters for documented fields
- **WHEN** a client calls `GET /v1/drivers?driver_number=1&session_key=9158`
- **THEN** the route SHALL pass those values to `DriverService.list_drivers` and respond `200` with a JSON array

#### Scenario: Route accepts repeated `driver_number` as an in-filter
- **WHEN** a client calls `GET /v1/drivers?driver_number=1&driver_number=11`
- **THEN** the route SHALL pass `driver_number=[1, 11]` to the service and the upstream URL SHALL contain `driver_number=1&driver_number=11`

#### Scenario: Route documents 502 and 504 responses
- **WHEN** the OpenAPI schema is generated for `GET /v1/drivers`
- **THEN** the `responses` map SHALL include entries for `200`, `422`, `502`, and `504`, each with a description and an example body

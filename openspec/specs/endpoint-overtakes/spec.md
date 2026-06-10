## ADDED Requirements

### Requirement: The system SHALL expose a typed `Overtake` Pydantic model

The system SHALL define `lapwise.models.overtakes.Overtake` mirroring OpenF1's `/overtakes` response shape.

#### Scenario: Overtake model fields match OpenF1's documented shape
- **WHEN** `Overtake` is introspected
- **THEN** it SHALL define at least: `date: datetime`, `meeting_key: int`, `overtaken_driver_number: int`, `overtaking_driver_number: int`, `position: int`, `session_key: int`
- **AND** the model's docstring SHALL note that data is only available during races and may be incomplete

### Requirement: The system SHALL expose an `OvertakeService.list_overtakes` method

The system SHALL define `lapwise.services.overtakes.OvertakeService` with an async `list_overtakes(...)` method returning `list[Overtake]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_overtakes(session_key=9636, overtaking_driver_number=63, overtaken_driver_number=4, position=1)`
- **THEN** the service SHALL call the client and return `list[Overtake]`

### Requirement: The system SHALL expose `GET /v1/overtakes`

The system SHALL register `GET /v1/overtakes` returning `list[Overtake]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/overtakes` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/overtakes` and noting race-only/incomplete data), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts the documented filters
- **WHEN** a client calls `GET /v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1`
- **THEN** the route SHALL forward those filters to the service and respond `200`

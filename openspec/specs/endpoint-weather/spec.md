## ADDED Requirements

### Requirement: The system SHALL expose a typed `Weather` Pydantic model

The system SHALL define `lapwise.models.weather.Weather` mirroring OpenF1's `/weather` response shape.

#### Scenario: Weather model fields match OpenF1's documented shape
- **WHEN** `Weather` is introspected
- **THEN** it SHALL define at least: `air_temperature: float | None`, `date: datetime`, `humidity: float | None`, `meeting_key: int`, `pressure: float | None`, `rainfall: int | bool | None`, `session_key: int`, `track_temperature: float | None`, `wind_direction: int | None`, `wind_speed: float | None`
- **AND** every field SHALL document its unit (°C, %, mbar, m/s, °)

### Requirement: The system SHALL expose a `WeatherService.list_weather` method

The system SHALL define `lapwise.services.weather.WeatherService` with an async `list_weather(...)` method returning `list[Weather]`.

#### Scenario: Service forwards filters and returns parsed models
- **WHEN** a caller invokes `list_weather(meeting_key=1208, wind_direction_gte=130, track_temperature_gte=52)`
- **THEN** the service SHALL call the client with `wind_direction>=130` and `track_temperature>=52` after translation and return `list[Weather]`

### Requirement: The system SHALL expose `GET /v1/weather`

The system SHALL register `GET /v1/weather` returning `list[Weather]`.

#### Scenario: Route is registered with rich OpenAPI metadata
- **WHEN** the OpenAPI schema is generated
- **THEN** `GET /v1/weather` SHALL appear under tag `OpenF1 wrappers` with summary, multi-paragraph description (linking to `https://api.openf1.org/v1/weather`), per-parameter descriptions, and response examples for `200`, `422`, `502`, `504`

#### Scenario: Route accepts multiple comparison filters in one query
- **WHEN** a client calls `GET /v1/weather?meeting_key=1208&wind_direction_gte=130&track_temperature_gte=52`
- **THEN** the upstream URL SHALL contain both `wind_direction>=130` and `track_temperature>=52`

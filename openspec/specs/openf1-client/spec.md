## ADDED Requirements

### Requirement: OpenF1Client SHALL provide async HTTP access to OpenF1

The system SHALL expose an `OpenF1Client` class that wraps `httpx.AsyncClient` and provides typed access to OpenF1's HTTP endpoints. The client SHALL be the only component permitted to perform network I/O against OpenF1.

#### Scenario: Client issues GET requests using configured base URL
- **WHEN** the client is asked to fetch a path like `drivers` with no filters
- **THEN** it SHALL issue a GET to `<base_url>/<path>` using the configured `httpx.AsyncClient`
- **AND** the base URL SHALL default to `https://api.openf1.org/v1` and be overridable via `Settings.openf1_base_url`

#### Scenario: Client deserializes JSON arrays into typed lists
- **WHEN** OpenF1 returns a 200 with a JSON array body
- **THEN** the client SHALL parse the body and return a `list[Model]` where `Model` is the Pydantic model supplied by the caller

#### Scenario: Client raises a typed error if the body is not a JSON array
- **WHEN** OpenF1 returns a 200 whose body is not a JSON array (e.g., an object, a string, malformed JSON)
- **THEN** the client SHALL raise `UpstreamError` with a category indicating decode failure

### Requirement: OpenF1Client SHALL translate hybrid filter syntax into OpenF1's native query syntax

The client SHALL accept filter parameters from callers in the wrapper's hybrid form and translate them to OpenF1's native operator syntax when constructing the upstream URL. Translation logic SHALL live in a separate `filters` module so it is unit-testable without HTTP.

#### Scenario: Equality filter is passed through unchanged
- **WHEN** a caller supplies `driver_number=4`
- **THEN** the upstream query string SHALL include `driver_number=4`

#### Scenario: Repeated-key in-filter is preserved as repeated keys
- **WHEN** a caller supplies `driver_number=[4, 81]`
- **THEN** the upstream query string SHALL include `driver_number=4&driver_number=81`

#### Scenario: Comparison suffixes translate to native operators
- **WHEN** a caller supplies any of `stop_duration_lt=2.3`, `position_lte=3`, `wind_direction_gte=130`, `lap_number_gt=10`
- **THEN** the upstream query string SHALL include `stop_duration<2.3`, `position<=3`, `wind_direction>=130`, `lap_number>10` respectively

#### Scenario: None values are omitted from the upstream query
- **WHEN** a caller supplies a filter whose value is `None`
- **THEN** the upstream query string SHALL NOT include that key at all

#### Scenario: Boolean and numeric values are serialized in OpenF1's expected form
- **WHEN** a caller supplies `is_pit_out_lap=False` or `lap_number=8`
- **THEN** the upstream query string SHALL include `is_pit_out_lap=false` and `lap_number=8` (lowercase booleans, no quoting of numbers)

### Requirement: OpenF1Client SHALL map upstream errors to a standardized error envelope

The client SHALL classify upstream failures and raise `UpstreamError` with a category so the FastAPI exception handler can return the agreed status code and response body.

#### Scenario: Upstream 5xx maps to a Bad Gateway category
- **WHEN** OpenF1 returns any 5xx response
- **THEN** the client SHALL raise `UpstreamError` with category `bad_gateway` and SHALL include the upstream status and a truncated body excerpt

#### Scenario: Upstream timeout maps to a Gateway Timeout category
- **WHEN** the upstream call raises `httpx.TimeoutException`
- **THEN** the client SHALL raise `UpstreamError` with category `gateway_timeout`

#### Scenario: Upstream network error maps to a Bad Gateway category
- **WHEN** the upstream call raises `httpx.ConnectError` or any other transport-level `httpx.HTTPError` not covered above
- **THEN** the client SHALL raise `UpstreamError` with category `bad_gateway`

#### Scenario: Upstream 4xx is forwarded with the same status
- **WHEN** OpenF1 returns a 4xx response
- **THEN** the client SHALL raise `UpstreamError` with category `forwarded` and the original status code so the exception handler can echo that status

### Requirement: OpenF1Client SHALL be lifecycle-managed by the FastAPI app

The system SHALL create exactly one `OpenF1Client` per process and dispose of it on shutdown.

#### Scenario: Client is created during app startup
- **WHEN** the FastAPI app starts via its lifespan handler
- **THEN** a single `OpenF1Client` instance SHALL be instantiated and stored on `app.state`

#### Scenario: Client is closed during app shutdown
- **WHEN** the FastAPI app shuts down via its lifespan handler
- **THEN** the client's `aclose()` method SHALL be awaited

#### Scenario: Request handlers receive the shared client via DI
- **WHEN** a route handler depends on `get_openf1_client`
- **THEN** the dependency SHALL return the same `OpenF1Client` instance for the lifetime of the app

### Requirement: OpenF1Client SHALL be configurable via settings

The client's HTTP behavior SHALL be configurable via the application `Settings` object so timeouts and base URLs can be tuned without code changes.

#### Scenario: Settings override the default base URL
- **WHEN** `Settings.openf1_base_url` is set to a non-default URL
- **THEN** the client SHALL issue requests against that base URL

#### Scenario: Settings override the default timeout
- **WHEN** `Settings.openf1_timeout_seconds` is set
- **THEN** the underlying `httpx.AsyncClient` SHALL be configured with that timeout for connect, read, write, and pool operations

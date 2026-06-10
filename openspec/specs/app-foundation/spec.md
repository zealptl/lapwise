## ADDED Requirements

### Requirement: The FastAPI application SHALL be defined via an application factory

The system SHALL expose a `create_app()` factory in `lapwise.main` that constructs and returns the `FastAPI` instance. The factory SHALL configure OpenAPI metadata, register routers, install exception handlers, and wire the application lifespan.

#### Scenario: Factory returns a configured FastAPI instance
- **WHEN** `create_app()` is called
- **THEN** it SHALL return a `FastAPI` object with non-empty `title`, `version`, and `description`
- **AND** the title SHALL be a human-readable name for the wrapper API
- **AND** the description SHALL state that the API wraps OpenF1's historical tier

#### Scenario: Module-level `app` is the result of the factory
- **WHEN** `lapwise.main` is imported
- **THEN** the module SHALL expose `app = create_app()` so ASGI servers can target `lapwise.main:app`

### Requirement: The application SHALL register a v1 router and an analysis router

The application SHALL register two routers at startup: one for the OpenF1 wrappers and one reserved for future analysis endpoints.

#### Scenario: The v1 router is mounted at `/v1`
- **WHEN** the app is created
- **THEN** an `APIRouter` with prefix `/v1` and tag `OpenF1 wrappers` SHALL be registered
- **AND** the router SHALL have a no-op auth dependency attached so an auth dependency can be swapped in later without changing route signatures

#### Scenario: The analysis router is mounted at `/v1/analysis`
- **WHEN** the app is created
- **THEN** an `APIRouter` with prefix `/v1/analysis` and tag `Analysis` SHALL be registered
- **AND** the router MAY have zero endpoints in this change

### Requirement: The application SHALL load settings from environment variables

The system SHALL provide a `Settings` model backed by `pydantic-settings` that loads configuration from environment variables and `.env`.

#### Scenario: Default settings are usable without any environment variables
- **WHEN** `Settings()` is instantiated with no environment variables set
- **THEN** `openf1_base_url` SHALL default to `https://api.openf1.org/v1`
- **AND** `openf1_timeout_seconds` SHALL default to a positive float (recommended 10.0)

#### Scenario: Environment variables override defaults
- **WHEN** the environment defines `OPENF1_BASE_URL` or `OPENF1_TIMEOUT_SECONDS`
- **THEN** the corresponding fields on `Settings` SHALL reflect the environment values

#### Scenario: Settings are accessed via a cached dependency
- **WHEN** route handlers depend on `get_settings`
- **THEN** the dependency SHALL return the same `Settings` instance across requests (cached via `functools.lru_cache` or equivalent)

### Requirement: The application SHALL provide dependency providers for client and services

The system SHALL expose FastAPI dependency providers in `lapwise.deps` so route handlers receive their collaborators by injection rather than by direct instantiation.

#### Scenario: `get_openf1_client` returns the app-state client
- **WHEN** any handler depends on `get_openf1_client`
- **THEN** the dependency SHALL return the `OpenF1Client` stored on `app.state` during lifespan startup

#### Scenario: `get_<resource>_service` returns a fresh service wrapping the shared client
- **WHEN** any handler depends on a service provider such as `get_driver_service`
- **THEN** the dependency SHALL return a new instance of the resource's service class, constructed with the shared `OpenF1Client`

#### Scenario: `get_auth` is a no-op dependency by default
- **WHEN** any handler depends on `get_auth`
- **THEN** the dependency SHALL return `None` and SHALL NOT reject the request
- **AND** the dependency's signature SHALL allow a later replacement that returns an authenticated principal without changes to route signatures

### Requirement: The application SHALL handle UpstreamError uniformly across all endpoints

The system SHALL register a single exception handler for `UpstreamError` that translates each error category to the agreed HTTP status and response envelope.

#### Scenario: bad_gateway category yields a 502 with the standard envelope
- **WHEN** an endpoint raises `UpstreamError(category="bad_gateway", upstream_status=503, upstream_message="...")`
- **THEN** the response SHALL be HTTP 502 with body `{ "detail": "OpenF1 upstream error", "upstream_status": 503, "upstream_message": "..." }`

#### Scenario: gateway_timeout category yields a 504
- **WHEN** an endpoint raises `UpstreamError(category="gateway_timeout", ...)`
- **THEN** the response SHALL be HTTP 504 with the standard envelope

#### Scenario: forwarded category yields the original upstream status
- **WHEN** an endpoint raises `UpstreamError(category="forwarded", upstream_status=404, ...)`
- **THEN** the response SHALL be HTTP 404 with the standard envelope

### Requirement: The application SHALL expose a health-check endpoint

The system SHALL expose `GET /healthz` returning a static body indicating the app is up. This endpoint SHALL NOT call OpenF1.

#### Scenario: Health check responds 200 without touching OpenF1
- **WHEN** a client sends `GET /healthz`
- **THEN** the response SHALL be HTTP 200 with body `{ "status": "ok" }`
- **AND** the `OpenF1Client` SHALL NOT be invoked

### Requirement: The application SHALL publish rich OpenAPI metadata

The system SHALL configure the FastAPI app's OpenAPI metadata so the generated `/openapi.json` and `/docs` describe the wrapper API clearly.

#### Scenario: OpenAPI tags carry descriptions
- **WHEN** the OpenAPI schema is generated
- **THEN** the `tags` section SHALL include entries for `OpenF1 wrappers` and `Analysis`, each with a non-empty description

#### Scenario: OpenAPI servers list includes a default
- **WHEN** the OpenAPI schema is generated
- **THEN** the `servers` section SHALL include at least one entry describing where the API runs locally (e.g. `http://localhost:8000`)

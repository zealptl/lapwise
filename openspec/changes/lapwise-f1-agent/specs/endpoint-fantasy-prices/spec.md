## ADDED Requirements

### Requirement: GET /v1/fantasy/prices endpoint exists
The Lapwise FastAPI service SHALL expose `GET /v1/fantasy/prices` returning a JSON object with 2025 F1 Fantasy prices for all drivers and constructors. The data SHALL be hardcoded in the source as a Python dict (updated manually each season).

#### Scenario: Returns price list for drivers and constructors
- **WHEN** `GET /v1/fantasy/prices` is called with a valid JWT
- **THEN** response SHALL be a JSON object with two keys: `"drivers"` (list of driver entries with name and price in millions) and `"constructors"` (list of constructor entries with name and price in millions)

#### Scenario: Response includes all 20 drivers and 10 constructors
- **WHEN** `GET /v1/fantasy/prices` is called
- **THEN** the `"drivers"` array SHALL contain 20 entries and `"constructors"` SHALL contain 10 entries for the 2025 season

### Requirement: Fantasy prices require authentication
`GET /v1/fantasy/prices` SHALL require a valid Cognito JWT in the `Authorization: Bearer` header.

#### Scenario: Unauthenticated request is rejected
- **WHEN** `GET /v1/fantasy/prices` is called without an Authorization header
- **THEN** response SHALL be HTTP 401

### Requirement: Fantasy prices endpoint is documented in OpenAPI spec
The `/v1/fantasy/prices` endpoint SHALL have a FastAPI `summary`, `description`, and typed response model in the OpenAPI spec so the AgentCore Gateway can present it as a usable tool.

#### Scenario: OpenAPI spec includes prices endpoint
- **WHEN** `GET /openapi.json` is called
- **THEN** the `/v1/fantasy/prices` path SHALL appear with summary "Get current F1 Fantasy prices" and a response schema describing the drivers and constructors arrays

### Requirement: Price data structure includes driver number and team
Each driver entry in the prices response SHALL include: `driver_number`, `full_name`, `abbreviation`, `team`, and `price_millions`. Each constructor entry SHALL include: `name`, `abbreviation`, and `price_millions`.

#### Scenario: Driver price entry has required fields
- **WHEN** `GET /v1/fantasy/prices` is called
- **THEN** each driver entry SHALL have `driver_number`, `full_name`, `abbreviation`, `team`, and `price_millions` fields

#### Scenario: Constructor price entry has required fields
- **WHEN** `GET /v1/fantasy/prices` is called
- **THEN** each constructor entry SHALL have `name`, `abbreviation`, and `price_millions` fields

## MODIFIED Requirements

### Requirement: The application SHALL publish rich OpenAPI metadata
The system SHALL configure the FastAPI app's OpenAPI metadata so the generated `/openapi.json` and `/docs` describe the wrapper API clearly. The `/openapi.json` endpoint SHALL be accessible without authentication so the AgentCore Gateway can fetch it at configuration time.

#### Scenario: OpenAPI tags carry descriptions
- **WHEN** the OpenAPI schema is generated
- **THEN** the `tags` section SHALL include entries for `OpenF1 wrappers`, `Analysis`, and `Fantasy`, each with a non-empty description

#### Scenario: OpenAPI servers list includes a default
- **WHEN** the OpenAPI schema is generated
- **THEN** the `servers` section SHALL include at least one entry describing where the API runs locally (e.g. `http://localhost:8000`)

#### Scenario: /openapi.json is accessible without authentication
- **WHEN** a request is made to `GET /openapi.json` without an Authorization header
- **THEN** the response SHALL be HTTP 200 with the full OpenAPI schema JSON
- **AND** the API Gateway resource policy or Lambda authorizer SHALL be configured to allow unauthenticated access to this path specifically

#### Scenario: /openapi.json reflects all routes including analysis and fantasy endpoints
- **WHEN** the Lapwise service is deployed with the new analysis and pricing endpoints
- **THEN** `GET /openapi.json` SHALL include paths for all `/v1/analysis/*` endpoints and `/v1/fantasy/prices`

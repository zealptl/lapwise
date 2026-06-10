## ADDED Requirements

### Requirement: Gateway uses OpenAPI target pointing at Lapwise openapi.json
The AgentCore Gateway SHALL be configured with `--type open-api-schema` and its target URL SHALL point at the Lapwise FastAPI's `/openapi.json` endpoint, making all Lapwise routes available as agent tools.

#### Scenario: Gateway is provisioned with OpenAPI target
- **WHEN** the AgentCore Gateway is created
- **THEN** its target type SHALL be `open-api-schema` and the spec URL SHALL be `https://<lapwise-api-gateway-url>/openapi.json`

#### Scenario: All Lapwise routes appear as tools in the gateway catalog
- **WHEN** the gateway catalog is queried
- **THEN** it SHALL include tools for all existing Lapwise endpoints (drivers, sessions, meetings, laps, stints, pit, position, starting_grid, overtakes, session_result, weather, championship_drivers, championship_teams), all 8 new analysis endpoints, and the fantasy prices endpoint

### Requirement: Inbound auth is CUSTOM_JWT using Cognito M2M client A
The gateway SHALL validate inbound requests using `CUSTOM_JWT` authorization with the Cognito User Pool and M2M app client A as the authorized audience.

#### Scenario: Valid JWT from client A is accepted
- **WHEN** agent sends a request with a valid Cognito JWT issued by client A
- **THEN** gateway SHALL process the request

#### Scenario: Request without JWT is rejected
- **WHEN** a request arrives at the gateway without an Authorization header
- **THEN** gateway SHALL return HTTP 401

#### Scenario: JWT from unknown client is rejected
- **WHEN** a request arrives with a JWT not issued for the gateway audience
- **THEN** gateway SHALL return HTTP 403

### Requirement: Outbound auth uses Cognito client credentials grant via M2M client B
The gateway SHALL attach a Cognito JWT to downstream Lapwise API requests by performing an OAuth 2.0 client credentials grant using M2M app client B's `client_id` and `client_secret`.

#### Scenario: Gateway attaches Authorization header to Lapwise requests
- **WHEN** gateway calls any Lapwise endpoint
- **THEN** the downstream request SHALL include an `Authorization: Bearer <token>` header using a token obtained from M2M client B's client credentials flow

### Requirement: Semantic search is enabled on the gateway
The gateway SHALL have `x_amz_bedrock_agentcore_search` enabled to improve tool selection accuracy when the tool catalog contains more than 20 tools.

#### Scenario: Semantic search is active
- **WHEN** the agent queries the gateway for tools matching a fantasy recommendation intent
- **THEN** the gateway SHALL return semantically relevant tools (e.g., analysis endpoints) even if the query does not exactly match endpoint names

### Requirement: Agent can obtain and cache gateway JWT
The agent code SHALL implement a helper that obtains a Cognito JWT via client credentials grant using M2M client A's credentials (from environment variables) and caches the token until its expiry.

#### Scenario: Token is fetched on first gateway call
- **WHEN** agent makes its first gateway tool call in a session
- **THEN** agent SHALL fetch a Cognito JWT from the Cognito token endpoint using client A credentials

#### Scenario: Cached token is reused within expiry window
- **WHEN** agent makes a second gateway tool call within the token's validity period
- **THEN** agent SHALL reuse the cached token without fetching a new one

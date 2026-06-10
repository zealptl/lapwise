## 1. Lapwise API — New Endpoints

- [ ] 1.1 Add `GET /v1/analysis/driver-pace-profile` FastAPI route with typed request params (`driver_number`, `circuit_key`, `year`, `include_circuit_history`) and Pydantic response model
- [ ] 1.2 Implement `driver-pace-profile` handler: aggregate lap and stint data from existing OpenF1 client; when `include_circuit_history=true`, fetch same circuit for year-1 and year-2
- [ ] 1.3 Add `GET /v1/analysis/dnf-rates` route and handler: compute DNF rates per driver/constructor from session_result data; support `last_n_races` and `include_circuit_history` params
- [ ] 1.4 Add `GET /v1/analysis/fastest-lap-candidates` route and handler: rank drivers by historical fastest-lap frequency at circuit using laps data
- [ ] 1.5 Add `GET /v1/analysis/overtake-profile` route and handler: aggregate overtakes and positions-gained per driver using overtakes + starting_grid + session_result data
- [ ] 1.6 Add `GET /v1/analysis/circuit-profile` route and handler: compute overtake difficulty, pitstop frequency, tyre strategies, safety car probability from laps + pit + weather data
- [ ] 1.7 Add `GET /v1/analysis/championship-context` route and handler: return standings + per-driver points trajectory using championship_drivers + championship_teams data; support `last_n_races`
- [ ] 1.8 Add `GET /v1/analysis/qualifying-trends` route and handler: return per-driver average qualifying position and Q3 frequency from starting_grid data
- [ ] 1.9 Add `GET /v1/analysis/constructor-pitstop` route and handler: return per-constructor pit stop statistics with F1 Fantasy threshold frequency breakdown using pit data
- [ ] 1.10 Add `GET /v1/fantasy/prices` route with hardcoded 2025 driver and constructor prices (20 drivers, 10 constructors); define `DriverPrice` and `ConstructorPrice` Pydantic models with `driver_number`, `full_name`, `abbreviation`, `team`, `price_millions`
- [ ] 1.11 Register all new analysis routes on the `/v1/analysis` router and prices route on a `/v1/fantasy` router; add `Fantasy` tag with description to OpenAPI metadata
- [ ] 1.12 Add FastAPI `summary` and `description` to every new endpoint so `/openapi.json` provides full documentation for gateway tool catalog

## 2. Lapwise API — OpenAPI Public Access

- [ ] 2.1 Verify `/openapi.json` is included in the API Gateway resource policy or Lambda authorizer allow-list so it is accessible without authentication
- [ ] 2.2 Add integration test asserting `GET /openapi.json` returns HTTP 200 without an Authorization header and that the response includes all new analysis and fantasy paths

## 3. Cognito M2M App Clients

- [ ] 3.1 Create Cognito M2M app client A (Agent→Gateway) in the existing Lapwise User Pool: enable client credentials grant; assign appropriate resource server scopes
- [ ] 3.2 Store client A `client_id` and `client_secret` in AWS Secrets Manager under a path like `lapwise/agent/cognito-client-a`
- [ ] 3.3 Create Cognito M2M app client B (Gateway→Lapwise) in the same User Pool: enable client credentials grant; assign Lapwise API resource server scopes
- [ ] 3.4 Store client B `client_id` and `client_secret` in AWS Secrets Manager under `lapwise/agent/cognito-client-b`
- [ ] 3.5 Verify that a token issued by client A is NOT accepted by the Lapwise API Gateway authorizer (wrong audience); document in the agent README

## 4. AgentCore Infrastructure Setup

- [ ] 4.1 Install and configure the `agentcore` CLI locally; authenticate with AWS us-east-1
- [ ] 4.2 Create AgentCore Gateway via `agentcore gateway create --type open-api-schema --spec-url <lapwise-openapi-url>` with CUSTOM_JWT inbound auth (Cognito User Pool + client A audience) and Cognito client credentials outbound auth (client B credentials)
- [ ] 4.3 Enable semantic search on the gateway (`x_amz_bedrock_agentcore_search`)
- [ ] 4.4 Create AgentCore Memory resource with SUMMARIZATION strategy (365-day expiry) and USER_PREFERENCE strategy (365-day expiry, passive + explicit extraction); note the Memory resource ID
- [ ] 4.5 Create AgentCore Observability resource with CloudWatch + X-Ray enabled; confirm CloudWatch log group is created in us-east-1
- [ ] 4.6 Record all resource ARNs/IDs (gateway, memory, observability) — needed for `agentcore.json`

## 5. Agent Project Scaffold

- [ ] 5.1 Create `agent/` directory at repo root; run `agentcore create LapwiseF1Agent --framework GoogleADK --region us-east-1` inside it (or manually scaffold if CLI doesn't support this exactly)
- [ ] 5.2 Verify `agent/agentcore/agentcore.json` is created; set `build.type = "CodeZip"`, `model = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"`, and reference memory/gateway/observability resource IDs from task 4.6
- [ ] 5.3 Add Python dependencies to `agent/` project: `bedrock-agentcore`, `bedrock-agentcore-starter-toolkit`, `google-adk`, `boto3`; create `requirements.txt` or `pyproject.toml`

## 6. Agent Core Implementation

- [ ] 6.1 Create `agent/app/LapwiseF1Agent/main.py`; define the GoogleADK `Agent` with model ID, system prompt (collaborative style, three-scenario output, scoring rules awareness, chip awareness)
- [ ] 6.2 Write the full system prompt: include F1 Fantasy scoring priority order (DNF avoidance, positions gained, constructor pitstop, fastest lap, overtakes, qualifying, boost), three output scenarios (best, value, risk-tolerant), boost pick guidance, and transparency instruction for historical data
- [ ] 6.3 Implement `CognitoTokenCache` helper class: fetches JWT via client credentials grant using `COGNITO_CLIENT_A_ID` / `COGNITO_CLIENT_A_SECRET` env vars; caches until expiry; returns `None` when env vars are absent
- [ ] 6.4 Implement gateway tool registration at agent startup: when `AGENTCORE_GATEWAY_ENDPOINT_URL` is set, load tool definitions from gateway and register them; log a warning and skip when not set
- [ ] 6.5 Implement `save_user_preference(preference: str)` as a `@function_tool`: calls MemoryClient to store the preference; when `MEMORY_ID` is None, no-ops silently
- [ ] 6.6 Implement `clear_user_preferences()` as a `@function_tool`: allows user to wipe stored preferences via MemoryClient; no-op when `MEMORY_ID` is None
- [ ] 6.7 Implement `load_session_context(session_id: str) -> dict` helper: calls `MemoryClient.retrieve()` for SUMMARIZATION and USER_PREFERENCE strategies; returns empty dict when `MEMORY_ID` is None; formats results for system prompt injection
- [ ] 6.8 Implement session entrypoint: accept `session_id` from request body (generate UUID v4 if absent); call `load_session_context`; prepend memory context to the agent's per-turn system context; invoke the GoogleADK agent; return response
- [ ] 6.9 Wrap the agent with `BedrockAgentCoreApp` and expose as the Lambda handler entry point

## 7. Agent Observability Wiring

- [ ] 7.1 Add X-Ray SDK instrumentation to `main.py`: create a root segment per session with `session_id` as an annotation
- [ ] 7.2 Instrument MemoryClient `retrieve` and `store` calls with X-Ray subsegments labeled `memory.retrieve` and `memory.store`
- [ ] 7.3 Instrument each gateway tool call with an X-Ray subsegment labeled with the tool name
- [ ] 7.4 Verify CloudWatch structured logs are emitted per session (session_id, user_id, turn_count, latency)

## 8. Local Development & Testing

- [ ] 8.1 Run `agentcore dev` from `agent/` directory; confirm agent starts without errors when `MEMORY_ID` and `AGENTCORE_GATEWAY_ENDPOINT_URL` are absent
- [ ] 8.2 Write a smoke test script that sends a test message ("What drivers should I pick for Monaco?") to the local dev server and asserts a non-empty response
- [ ] 8.3 Add unit tests for `CognitoTokenCache`: mock Cognito token endpoint; assert token is fetched on first call and cached on second call
- [ ] 8.4 Add unit tests for `load_session_context`: mock MemoryClient; assert empty dict is returned when `MEMORY_ID` is None; assert memory results are injected when available
- [ ] 8.5 Add unit tests for `save_user_preference` and `clear_user_preferences`: assert no-op when `MEMORY_ID` is None; assert MemoryClient is called with correct args when set

## 9. Deployment

- [ ] 9.1 Set environment variables in `agentcore.json` or via agentcore CLI: `MEMORY_ID`, `AGENTCORE_GATEWAY_ENDPOINT_URL`, `COGNITO_CLIENT_A_ID` (from Secrets Manager reference), `COGNITO_CLIENT_A_SECRET` (from Secrets Manager reference)
- [ ] 9.2 Run `agentcore deploy` from `agent/` directory; confirm Lambda function, AgentCore Agent runtime, and IAM roles are created in us-east-1
- [ ] 9.3 Smoke test deployed agent: invoke with a valid user Cognito JWT, ask a fantasy question, assert structured three-scenario response
- [ ] 9.4 Verify X-Ray traces appear in AWS Console for the session
- [ ] 9.5 Verify CloudWatch log group `LapwiseF1Agent` has entries after the smoke test invocation
- [ ] 9.6 Verify memory: run two sessions; in session 2 confirm the agent recalls a preference stated in session 1
- [ ] 9.7 Document rollback steps in `agent/README.md`: `agentcore destroy` removes agent stack; Lapwise API and `infra/` CDK stack are unaffected

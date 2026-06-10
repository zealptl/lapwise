## 1. Lapwise API — New Endpoints

- [x] 1.1 Add `GET /v1/analysis/driver-pace-profile` FastAPI route with typed request params (`driver_number`, `circuit_key`, `year`, `include_circuit_history`) and Pydantic response model
- [x] 1.2 Implement `driver-pace-profile` handler: aggregate lap and stint data from existing OpenF1 client; when `include_circuit_history=true`, fetch same circuit for year-1 and year-2
- [x] 1.3 Add `GET /v1/analysis/dnf-rates` route and handler: compute DNF rates per driver/constructor from session_result data; support `last_n_races` and `include_circuit_history` params
- [x] 1.4 Add `GET /v1/analysis/fastest-lap-candidates` route and handler: rank drivers by historical fastest-lap frequency at circuit using laps data
- [x] 1.5 Add `GET /v1/analysis/overtake-profile` route and handler: aggregate overtakes and positions-gained per driver using overtakes + starting_grid + session_result data
- [x] 1.6 Add `GET /v1/analysis/circuit-profile` route and handler: compute overtake difficulty, pitstop frequency, tyre strategies, safety car probability from laps + pit + weather data
- [x] 1.7 Add `GET /v1/analysis/championship-context` route and handler: return standings + per-driver points trajectory using championship_drivers + championship_teams data; support `last_n_races`
- [x] 1.8 Add `GET /v1/analysis/qualifying-trends` route and handler: return per-driver average qualifying position and Q3 frequency from starting_grid data
- [x] 1.9 Add `GET /v1/analysis/constructor-pitstop` route and handler: return per-constructor pit stop statistics with F1 Fantasy threshold frequency breakdown using pit data
- [x] 1.10 Add `GET /v1/fantasy/prices` route with hardcoded 2025 driver and constructor prices (20 drivers, 10 constructors); define `DriverPrice` and `ConstructorPrice` Pydantic models with `driver_number`, `full_name`, `abbreviation`, `team`, `price_millions`
- [x] 1.11 Register all new analysis routes on the `/v1/analysis` router and prices route on a `/v1/fantasy` router; add `Fantasy` tag with description to OpenAPI metadata
- [x] 1.12 Add FastAPI `summary` and `description` to every new endpoint so `/openapi.json` provides full documentation for gateway tool catalog

## 2. Lapwise API — OpenAPI Public Access

- [ ] 2.1 In `infra/lib/lapwise-stack.ts`, add `HttpNoneAuthorizer` route overrides for `GET /openapi.json` and `GET /docs` (same pattern as the existing `/healthz` exemption on line 80); redeploy `infra/` — the AgentCore Gateway fetches `/openapi.json` without a token to build its tool catalog
- [ ] 2.2 Add integration test asserting `GET /openapi.json` returns HTTP 200 without an Authorization header and that the response includes all new analysis and fantasy paths

## 3. Cognito M2M App Clients

- [ ] 3.1 Create Cognito M2M app client A (Agent→Gateway) in the existing Lapwise User Pool: enable client credentials grant; assign appropriate resource server scopes
- [ ] 3.2 Store client A `client_id` and `client_secret` in AWS Secrets Manager under `lapwise/agent/cognito-client-a`
- [ ] 3.3 Create Cognito M2M app client B (Gateway→Lapwise) in the same User Pool: enable client credentials grant; assign Lapwise API resource server scopes
- [ ] 3.4 Store client B `client_id` and `client_secret` in AWS Secrets Manager under `lapwise/agent/cognito-client-b`
- [ ] 3.5 In `infra/lib/lapwise-stack.ts`, add client B's `userPoolClientId` to the `jwtAudience` array on `HttpJwtAuthorizer` (line 56) so Gateway→Lapwise tokens are accepted; redeploy `infra/`
- [ ] 3.6 Verify that a token issued by client A is NOT accepted by the Lapwise API Gateway authorizer (wrong audience); document in the agent README

## 4. AgentCore Infrastructure Setup

- [ ] 4.1 Install and configure the `agentcore` CLI locally; authenticate with AWS us-east-1; run `agentcore --version` and confirm v0.9.0 or later before proceeding — scaffold structure and flag names differ in older versions
- [ ] 4.2 Create AgentCore Gateway named `LapwiseGateway` via `agentcore gateway create --name LapwiseGateway --type open-api-schema --spec-url <lapwise-openapi-url>` with CUSTOM_JWT inbound auth (Cognito User Pool + `LapwiseAppClient` audience) and Cognito client credentials outbound auth (client B credentials); the injected env var will be `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL`
- [ ] 4.3 Enable semantic search on the gateway (`x_amz_bedrock_agentcore_search`)
- [ ] 4.4 Create AgentCore Memory resource with SUMMARY strategy (365-day expiry) and USER_PREFERENCE strategy (365-day expiry); note the Memory resource ID — `StrategyType.SUMMARY` is the correct SDK enum value (not SUMMARIZATION)
- [ ] 4.5 Create AgentCore Observability resource with CloudWatch + X-Ray enabled; confirm CloudWatch log group is created in us-east-1
- [ ] 4.6 Record all resource ARNs/IDs (gateway, memory, observability) — needed for `agentcore.json`

## 5. Agent Project Scaffold

- [ ] 5.1 From repo root, run `agentcore create --name LapwiseF1Agent --framework GoogleADK --model-provider Bedrock --build CodeZip --memory none` to scaffold `LapwiseF1Agent/`; move or symlink into `agent/` directory; verify `aws-targets.json` has `us-east-1` before deploying — `--memory none` because memory is wired manually via `AgentCoreMemoryService`
- [ ] 5.2 Verify `agent/agentcore/agentcore.json` is created; set `build.type = "CodeZip"`, `model = "anthropic.claude-sonnet-4-6"`, and reference memory/gateway/observability resource IDs from task 4.6
- [ ] 5.3 Add IAM permission grants to the agentcore project for: `secretsmanager:GetSecretValue` on the client A secret ARN, `bedrock:InvokeModel` on `anthropic.claude-sonnet-4-6`, `bedrock-agentcore:RetrieveMemoryRecords` on the Memory resource ARN, `bedrock-agentcore:CreateMemorySessionEvent` on the Memory resource ARN — via `agentcore add policy` or `agentcore.json` `iamPermissions` block
- [ ] 5.4 Add Python dependencies to `agent/` project: `bedrock-agentcore`, `bedrock-agentcore-starter-toolkit`, `google-adk`, `boto3`; create `requirements.txt` or `pyproject.toml`

## 6. Agent Core Implementation

- [ ] 6.1 Create `agent/app/LapwiseF1Agent/main.py`; add imports: `from google.adk.tools import preload_memory`, `from google.adk.memory.base_memory_service import BaseMemoryService, SearchMemoryResponse`, `from google.adk.memory.memory_entry import MemoryEntry`, `from google.adk.runners import Runner`; define the GoogleADK `Agent` with model ID `anthropic.claude-sonnet-4-6`, system prompt, and `preload_memory` in the tools list
- [ ] 6.2 Write the full system prompt: include F1 Fantasy scoring priority order (DNF avoidance, positions gained, constructor pitstop, fastest lap, overtakes, qualifying, boost), three output scenarios (best, value, risk-tolerant), boost pick guidance, and transparency instruction for historical data
- [ ] 6.3 Implement `CognitoTokenCache` helper class: reads `COGNITO_CLIENT_A_SECRET_ARN` env var at cold start, fetches the actual secret from Secrets Manager via `boto3.client("secretsmanager").get_secret_value(SecretId=arn)`, caches the token until expiry; returns `None` when env var is absent (dev mode)
- [ ] 6.4 Implement gateway tool registration at agent startup: when `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` is set, load tool definitions from gateway using `CognitoTokenCache` for auth and register them on the agent; log a warning and skip when not set
- [ ] 6.5 Implement `save_user_preference(preference: str)` as a `@function_tool`: calls `MemoryClient.create_event(memory_id=MEMORY_ID, actor_id=user_id, session_id=session_id, messages=[(preference, "USER")])` to store the preference explicitly; when `MEMORY_ID` is None, no-ops silently
- [ ] 6.6 Implement `AgentCoreMemoryService(BaseMemoryService)` in `agent/app/LapwiseF1Agent/memory.py`:
  - Constructor: `MemoryClient(region_name=AWS_REGION)` — note `region_name` not `region`; cache strategy namespaces lazily via `client.get_memory_strategies(memory_id)` which returns `[{"type": ..., "namespaces": ["support/user/{actorId}/..."]}]`
  - `async def search_memory(self, *, app_name, user_id, query)` → call `get_last_k_turns(memory_id=..., actor_id=user_id, session_id=app_name, k=5)` for short-term; for each strategy namespace call `retrieve_memories(memory_id=..., namespace=template.replace("{actorId}", user_id), query=query, top_k=5)` for long-term; combine into `SearchMemoryResponse(memories=[MemoryEntry(...)])`
  - `async def add_session_to_memory(self, session)` → build `messages = [(part.text, "USER" if event.author == "user" else "ASSISTANT") for event in session.events for part in event.content.parts if part.text]`; call `client.create_event(memory_id=..., actor_id=session.user_id, session_id=session.id, messages=messages)`
  - Both methods must check `if not self._memory_id: return` as first line for dev-mode no-op
- [ ] 6.7 Wire `after_agent_callback`: implement `async def persist_session_callback(callback_context)` that calls `await callback_context.add_session_to_memory()`; assign `root_agent.after_agent_callback = persist_session_callback` — this is the explicit session-end write that triggers async SUMMARY + USER_PREFERENCE extraction (~1 minute background)
- [ ] 6.8 Implement session entrypoint: accept `session_id` from request body (generate UUID v4 if absent); construct `Runner(app_name="LapwiseF1Agent", agent=root_agent, memory_service=AgentCoreMemoryService(memory_id=os.getenv("MEMORY_ID")))`; create or resume session via `runner.session_service`; dispatch user message via `runner.run_async`; return final response text
- [ ] 6.9 Wrap the agent with `BedrockAgentCoreApp` and expose as the Lambda handler entry point

## 7. Agent Observability Wiring

- [ ] 7.1 Add X-Ray SDK instrumentation to `main.py`: create a root segment per session with `session_id` as an annotation
- [ ] 7.2 Instrument `add_session_to_memory` and `search_memory` calls with X-Ray subsegments labeled `memory.store` and `memory.retrieve`
- [ ] 7.3 Instrument each gateway tool call with an X-Ray subsegment labeled with the tool name
- [ ] 7.4 Verify CloudWatch structured logs are emitted per session (session_id, user_id, turn_count, latency)

## 8. Local Development & Testing

- [ ] 8.1 Run `agentcore dev --port 8080` from `agent/` directory; confirm agent starts without errors when `MEMORY_ID` and `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` are absent
- [ ] 8.2 Write a smoke test script that sends a test message ("What drivers should I pick for Monaco?") to `http://localhost:8080` and asserts a non-empty response; use `agentcore dev --port 8080` to pin the port so the script target never drifts
- [ ] 8.3 Add unit tests for `CognitoTokenCache`: mock Secrets Manager and Cognito token endpoint; assert secret is fetched once at cold start, token is cached on second call, and both return `None` when `COGNITO_CLIENT_A_SECRET_ARN` is absent
- [ ] 8.4 Add unit tests for `AgentCoreMemoryService`: mock `MemoryClient`; assert `search_memory` returns empty when `MEMORY_ID` is None; assert `add_session_to_memory` calls `create_event` with correct turn pairs when `MEMORY_ID` is set
- [ ] 8.5 Add unit tests for `save_user_preference`: assert no-op when `MEMORY_ID` is None; assert `MemoryClient.create_event` is called with correct args when set

## 9. Deployment

- [ ] 9.1 Set environment variables in `agentcore.json` or via agentcore CLI: `MEMORY_ID`, `COGNITO_CLIENT_A_SECRET_ARN` (the Secrets Manager ARN — not the raw secret), `COGNITO_CLIENT_A_ID`; the raw secret is fetched by `CognitoTokenCache` at cold start
- [ ] 9.2 Run `agentcore deploy` from `agent/` directory; confirm Lambda function, AgentCore Agent runtime, and IAM roles are created in us-east-1; verify `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` is present in the Lambda environment after deploy
- [ ] 9.3 Smoke test deployed agent: invoke with a valid user Cognito JWT (same token used for Lapwise API), ask a fantasy question, assert structured three-scenario response
- [ ] 9.4 Verify X-Ray traces appear in AWS Console for the session
- [ ] 9.5 Verify CloudWatch log group `LapwiseF1Agent` has entries after the smoke test invocation
- [ ] 9.6 Verify memory: run two sessions; in session 2 confirm the agent recalls a preference stated in session 1 (allow ~1 minute after session 1 ends for async USER_PREFERENCE extraction to complete)
- [ ] 9.7 Document rollback steps in `agent/README.md`: `agentcore destroy` removes agent stack; Lapwise API and `infra/` CDK stack are unaffected; document M2M client rotation runbook for client A and B independently

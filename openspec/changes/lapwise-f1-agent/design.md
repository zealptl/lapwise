## Context

Lapwise is a FastAPI service deployed on AWS Lambda + API Gateway, secured with Cognito JWT authentication. It wraps the OpenF1 API and exposes F1 race data through ~13 endpoints. The existing CDK stack in `infra/` manages Lambda, API Gateway, Cognito User Pool, and related IAM resources.

This design introduces a net-new AI agent layer: `LapwiseF1Agent`, a GoogleADK application hosted on AWS BedrockAgentCore. The agent sits in front of the Lapwise API and turns natural language questions ("What should my Monaco 2026 fantasy team be?") into structured, data-backed recommendations by calling Lapwise endpoints as tools.

The agent, gateway, memory, and observability resources are all managed by the `agentcore` CLI's own CDK stack — independent of the existing `infra/` stack. The Lapwise FastAPI service gains ~9 new routes but is otherwise unchanged. Two additive one-liners are required in `infra/`: an auth exemption for `/openapi.json` and `/docs`, and adding M2M client B to the JWT authorizer's audience list.

## Goals / Non-Goals

**Goals:**
- Deploy a working GoogleADK agent on BedrockAgentCore that answers F1 Fantasy questions
- Wire all Lapwise routes (existing + new analysis + pricing) as agent tools via an AgentCore Gateway
- Implement short-term (SUMMARY) and long-term (USER_PREFERENCE) memory with 365-day expiry
- Authenticate all three hops (User→Agent, Agent→Gateway, Gateway→Lapwise) using Cognito JWTs
- Add 8 analysis endpoints and 1 pricing endpoint to the Lapwise FastAPI service
- Provide full observability: CloudWatch + X-Ray traces at session, tool, and memory levels
- Handle `agentcore dev` gracefully (MEMORY_ID=None, AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL=None)

**Non-Goals:**
- A frontend or chat UI (agent is API-only for now)
- Real-time qualifying/race data ingestion (agent reasons from historical data)
- Automated CDK deployment pipelines (manual `agentcore deploy` for now)
- Structural changes to the existing `infra/` CDK stack (two additive one-liners are required but no new resources or architectural changes)
- Sharing Cognito M2M app clients between any two hops
- Agent-initiated push notifications or webhooks

## Decisions

### Decision 1: GoogleADK over LangGraph / raw Bedrock

GoogleADK provides a clean `@function_tool` decorator pattern, built-in multi-turn orchestration, and the `BedrockAgentCoreApp` runtime wrapper needed for AgentCore deployment. LangGraph would require more boilerplate for the same orchestration. Strands was considered but GoogleADK has the most mature BedrockAgentCore integration available at time of writing.

**Model**: `anthropic.claude-sonnet-4-6` (Claude Sonnet 4.6, direct Bedrock model ID — confirmed active in us-east-1). Chosen for strong reasoning, tool use, and cost-effectiveness over Opus. Haiku was considered but insufficient for multi-step fantasy reasoning.

### Decision 2: AgentCoreMemoryService(BaseMemoryService) for GoogleADK

AgentCore has native memory integration for some frameworks but **not** GoogleADK. The correct pattern, validated against the AgentCore workshop notebooks, uses GoogleADK's `BaseMemoryService` extension point:

1. **Implement `AgentCoreMemoryService(BaseMemoryService)`** with two methods:
   - `search_memory()` — calls `get_last_k_turns` (short-term verbatim buffer) + `retrieve_memories` per strategy namespace (long-term semantic extraction); returns a `SearchMemoryResponse` with combined `MemoryEntry` list
   - `add_session_to_memory()` — calls `create_event` with all `(text, role)` pairs from the session's events; this triggers async `SUMMARY` + `USER_PREFERENCE` extraction in the background (~1 minute)

2. **Wire `preload_memory` as an agent tool** — the built-in `google.adk.tools.preload_memory` tool calls `search_memory` before the model step and auto-injects a `<PAST_CONVERSATIONS>` block; the model never decides whether to search memory

3. **Wire `after_agent_callback`** — `root_agent.after_agent_callback = persist_session_callback` fires once the pipeline turn ends; `persist_session_callback` calls `await callback_context.add_session_to_memory()` which routes through `AgentCoreMemoryService.add_session_to_memory()` and calls `create_event`

4. **Wire the Runner** — `Runner(agent=root_agent, memory_service=AgentCoreMemoryService(memory_id=MEMORY_ID))`

Memory strategies: `SUMMARY` (short-term session context) and `USER_PREFERENCE` (long-term fantasy preferences). Note: the SDK enum is `StrategyType.SUMMARY`, not `SUMMARIZATION`.

**Memory ID** is passed via `MEMORY_ID` env var. When `MEMORY_ID` is `None` (local `agentcore dev`), `AgentCoreMemoryService` no-ops silently — the agent works without memory in dev mode.

**Session IDs**: UUID v4 generated per conversation (36 chars, above the 33-char minimum required by LTM extraction). Callers pass `session_id` in the request body; if absent, agent generates one.

### Decision 3: Two separate Cognito M2M app clients

Agent→Gateway (client A) and Gateway→Lapwise (client B) use **separate** Cognito app clients. This enables:
- Independent credential rotation without service disruption
- Separate CloudWatch audit trails per hop
- Principle of least privilege (client A only needs gateway scopes, client B only needs Lapwise API scopes)

Sharing a single client was considered and rejected on audit/rotation grounds.

### Decision 4: User→Agent auth reuses existing Lapwise Cognito User Pool

Users call the AgentCore agent endpoint with their existing Lapwise Cognito JWT — same token, no new login. The AgentCore runtime is configured to trust the same Cognito User Pool with `LapwiseAppClient` as the expected audience. No new app client is needed for this hop.

The Lapwise API Gateway authorizer currently validates `aud` against `[LapwiseAppClient.userPoolClientId]`. M2M client B tokens have a different `client_id` as their audience — so `infra/` must add client B's `client_id` to `jwtAudience` so Gateway→Lapwise requests are accepted. This is a one-line change to `lapwise-stack.ts`.

### Decision 5: Secrets Manager ARN in env vars, secret fetched at cold start

M2M client secrets are stored in AWS Secrets Manager. The Lambda env var holds the **ARN** of the secret, not the raw value — raw secrets in Lambda env vars appear in plaintext in the AWS console and CloudTrail. The `CognitoTokenCache` class fetches the actual secret via `boto3.client("secretsmanager").get_secret_value(SecretId=arn)` once at Lambda cold start and caches it in memory. This requires an explicit `secretsmanager:GetSecretValue` IAM grant on the Lambda execution role.

### Decision 6: AgentCore Gateway with OpenAPI target

The Gateway (`LapwiseGateway`) is configured with `--type open-api-schema` pointing at `https://<lapwise-api-gateway>/openapi.json`. This means:
- All Lapwise routes (existing + new) are automatically available as tools without manual tool definitions
- The agent catalog stays in sync with the FastAPI spec automatically
- Semantic search (`x_amz_bedrock_agentcore_search`) is enabled because the catalog will have 20+ tools — semantic search improves tool selection accuracy at this scale

**Inbound auth**: CUSTOM_JWT (validates the agent's Cognito JWT from client A)
**Outbound auth**: Cognito client credentials grant (Gateway fetches tokens using client B credentials and attaches to downstream Lapwise requests)

The gateway fetches `/openapi.json` without a token — `infra/` must add a `HttpNoneAuthorizer` route override for `GET /openapi.json` and `GET /docs`.

**Gateway env var**: after `agentcore deploy`, the CLI injects `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` into the Lambda environment.

### Decision 7: agentcore CDK stack is separate from infra/ CDK stack

The `agentcore` CLI manages its own CDK stack for the agent Lambda, AgentCore resources, IAM roles, and observability. Merging it into `infra/` would create a tight coupling between the agent lifecycle and the core API infrastructure. Keeping stacks separate allows:
- Independent deploy/rollback of agent vs. API
- Clear ownership boundary (agentcore CLI owns agent infra)
- Simpler rollback: destroy agent stack without touching Lapwise API

### Decision 8: Analysis endpoints are FastAPI routes, not Lambda extensions

The 8 analysis endpoints aggregate data already available via existing Lapwise routes (e.g., laps, stints, pit). They are implemented as new FastAPI route handlers in the `service/` directory, reusing existing OpenF1 client wrapper code. They are NOT separate Lambda functions — the existing Lambda deployment pattern handles them automatically.

**`include_circuit_history` parameter**: Each analysis endpoint accepts an optional `include_circuit_history: bool = False` query param. When true, the endpoint fetches data for the same circuit from the previous 2 years in addition to the requested year — enabling the agent's historical reasoning capability.

### Decision 9: Fantasy prices endpoint is hardcoded JSON

`GET /v1/fantasy/prices` returns a static Python dict (2025 season prices) serialized as JSON. Prices change at the start of each season or after major mid-season price resets. A database or external source is not warranted for a static dataset; the file is updated manually each season. This is the simplest correct approach.

### Decision 10: Agent build type is CodeZip

`agentcore.json` sets `build.type = "CodeZip"` (zip artifact deployed to Lambda). Container image was considered but CodeZip has faster deploy cycles for a Python function of this size and complexity.

## Risks / Trade-offs

**[Risk] GoogleADK has no native AgentCore memory integration** → Mitigation: `AgentCoreMemoryService(BaseMemoryService)` pattern with `after_agent_callback` (Decision 2). Validated pattern from AgentCore workshop notebooks — risk is implementation complexity, not feasibility.

**[Risk] Memory not available during `agentcore dev`** → Mitigation: `AgentCoreMemoryService` no-ops when `MEMORY_ID` is None. Agent works fully without memory in dev mode; memory is a session enhancement not a hard dependency.

**[Risk] Gateway URL not available locally** → Mitigation: Gateway tool registration is skipped when `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` is None; a warning is logged. Local dev tests orchestration logic only.

**[Risk] OpenAPI target keeps tool catalog in sync, but spec changes could break tool calls** → Mitigation: Any breaking change to Lapwise FastAPI route signatures should be coordinated with a gateway re-registration (`agentcore gateway update`). The semantic search layer absorbs minor parameter renames.

**[Risk] Long-term memory extraction is async (~1 minute delay after session end)** → Mitigation: Short-term recall via `get_last_k_turns` is synchronous and available immediately within the same session. Long-term USER_PREFERENCE extraction is background-only; acceptable for fantasy preference use case.

**[Risk] 365-day memory expiry accumulates stale preferences** → Mitigation: Acceptable for fantasy preferences (low-stakes data). Manual cleanup via AgentCore console if needed.

**[Risk] Two Cognito M2M clients require manual rotation coordination** → Mitigation: Each client is rotated independently. Client A rotation does not affect Gateway→Lapwise auth. Document rotation runbook in agent README.

**[Trade-off] agentcore CDK stack separation means two separate deploy steps** → Accepted. Operational simplicity outweighs the slight inconvenience.

## Migration Plan

1. **Infra changes**: add `HttpNoneAuthorizer` for `GET /openapi.json` + `GET /docs` in `lapwise-stack.ts`; redeploy `infra/`
2. **Add analysis + pricing routes** to Lapwise FastAPI service; deploy via existing CI/CD
3. **Verify `/openapi.json`** is accessible without auth and reflects all new routes
4. **Create two Cognito M2M app clients** (A and B) in existing Cognito User Pool; store secrets in Secrets Manager; add client B's `client_id` to `jwtAudience` in `lapwise-stack.ts`; redeploy `infra/`
5. **Configure AgentCore Gateway** (`LapwiseGateway`) via `agentcore gateway create --name LapwiseGateway --type open-api-schema --spec-url <url>` with CUSTOM_JWT inbound auth and Cognito outbound auth
6. **Configure AgentCore Memory** via `agentcore memory create` with SUMMARY + USER_PREFERENCE strategies (365-day expiry)
7. **Configure AgentCore Observability** via `agentcore observability create` with CloudWatch + X-Ray
8. **Scaffold `agent/`** via `agentcore create --name LapwiseF1Agent --framework GoogleADK --model-provider Bedrock --build CodeZip --memory none`; add IAM grants for Secrets Manager, Bedrock, and Memory
9. **Implement `main.py`**: `AgentCoreMemoryService`, `preload_memory` tool, `after_agent_callback`, `CognitoTokenCache`, gateway tool registration
10. **Run `agentcore dev --port 8080`** — smoke test without memory
11. **Run `agentcore deploy`** — deploy to AWS; smoke test with memory; verify `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` env var is injected
12. **Rollback**: `agentcore destroy` removes agent stack; Lapwise API and `infra/` stack are untouched

## Open Questions

- Should the agent support streaming responses (SSE) or is request/response sufficient for v1? (Assumed: request/response for now)
- Should `agentcore dev` mock gateway tools from a local FastAPI instance? (Assumed: no — dev mode tests orchestration logic only; full tool integration tested post-deploy)
- Are the 8 analysis endpoints expected to be synchronous (compute inline) or async (queue + poll)? (Assumed: synchronous — data volumes are small enough for sub-second response)

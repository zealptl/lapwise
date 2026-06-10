## Context

Lapwise is a FastAPI service deployed on AWS Lambda + API Gateway, secured with Cognito JWT authentication. It wraps the OpenF1 API and exposes F1 race data through ~13 endpoints. The existing CDK stack in `infra/` manages Lambda, API Gateway, Cognito User Pool, and related IAM resources.

This design introduces a net-new AI agent layer: `LapwiseF1Agent`, a GoogleADK application hosted on AWS BedrockAgentCore. The agent sits in front of the Lapwise API and turns natural language questions ("What should my Monaco 2026 fantasy team be?") into structured, data-backed recommendations by calling Lapwise endpoints as tools.

The agent, gateway, memory, and observability resources are all managed by the `agentcore` CLI's own CDK stack — independent of the existing `infra/` stack. The Lapwise FastAPI service gains ~9 new routes but is otherwise unchanged.

## Goals / Non-Goals

**Goals:**
- Deploy a working GoogleADK agent on BedrockAgentCore that answers F1 Fantasy questions
- Wire all Lapwise routes (existing + new analysis + pricing) as agent tools via an AgentCore Gateway
- Implement short-term (SUMMARIZATION) and long-term (USER_PREFERENCE) memory with 365-day expiry
- Authenticate all three hops (User→Agent, Agent→Gateway, Gateway→Lapwise) using Cognito JWTs
- Add 8 analysis endpoints and 1 pricing endpoint to the Lapwise FastAPI service
- Provide full observability: CloudWatch + X-Ray traces at session, tool, and memory levels
- Handle `agentcore dev` gracefully (MEMORY_ID=None, AGENTCORE_GATEWAY_*_URL=None)

**Non-Goals:**
- A frontend or chat UI (agent is API-only for now)
- Real-time qualifying/race data ingestion (agent reasons from historical data)
- Automated CDK deployment pipelines (manual `agentcore deploy` for now)
- Modifying the existing `infra/` CDK stack
- Sharing Cognito M2M app clients between any two hops
- Agent-initiated push notifications or webhooks

## Decisions

### Decision 1: GoogleADK over LangGraph / raw Bedrock

GoogleADK provides a clean `@function_tool` decorator pattern, built-in multi-turn orchestration, and the `BedrockAgentCoreApp` runtime wrapper needed for AgentCore deployment. LangGraph would require more boilerplate for the same orchestration. Strands was considered but GoogleADK has the most mature BedrockAgentCore integration available at time of writing.

**Model**: `global.anthropic.claude-sonnet-4-5-20250929-v1:0` (Claude Sonnet 4.5 via Bedrock cross-region inference). Chosen for strong reasoning, tool use, and cost-effectiveness over Opus. Haiku was considered but insufficient for multi-step fantasy reasoning.

### Decision 2: BYO MemoryClient for GoogleADK

AgentCore has native memory integration for some frameworks but **not** GoogleADK. Rather than wait for native support, we wire memory manually:

1. **Session start**: call `MemoryClient.retrieve()` to load conversation summary + preferences → inject into system prompt context
2. **During session**: expose `save_user_preference()` as an agent `@function_tool` → agent calls it when user explicitly states a preference
3. **Session end**: AgentCore's SUMMARIZATION + USER_PREFERENCE extraction strategies run automatically on the full conversation turn list

This pattern is standard for non-natively-integrated frameworks and gives full control over what context the agent sees.

**Memory ID and session ID** are passed via environment variables. When `MEMORY_ID` is `None` (local `agentcore dev`), all MemoryClient calls are skipped without error.

**Session IDs**: UUID v4 generated per conversation (minimum 33 chars required by LTM extraction). Callers pass `session_id` in the request body; if absent, agent generates one.

### Decision 3: Two separate Cognito M2M app clients

Agent→Gateway (client A) and Gateway→Lapwise (client B) use **separate** Cognito app clients. This enables:
- Independent credential rotation without service disruption
- Separate CloudWatch audit trails per hop
- Principle of least privilege (client A only needs gateway scopes, client B only needs Lapwise API scopes)

Sharing a single client was considered and rejected on audit/rotation grounds.

### Decision 4: AgentCore Gateway with OpenAPI target

The Gateway is configured with `--type open-api-schema` pointing at `https://<lapwise-api-gateway>/openapi.json`. This means:
- All Lapwise routes (existing + new) are automatically available as tools without manual tool definitions
- The agent catalog stays in sync with the FastAPI spec automatically
- Semantic search (`x_amz_bedrock_agentcore_search`) is enabled because the catalog will have 20+ tools — semantic search improves tool selection accuracy at this scale

**Inbound auth**: CUSTOM_JWT (validates the agent's Cognito JWT from client A)
**Outbound auth**: Cognito client credentials grant (Gateway fetches tokens using client B credentials and attaches to downstream Lapwise requests)

### Decision 5: agentcore CDK stack is separate from infra/ CDK stack

The `agentcore` CLI manages its own CDK stack for the agent Lambda, AgentCore resources, IAM roles, and observability. Merging it into `infra/` would create a tight coupling between the agent lifecycle and the core API infrastructure. Keeping stacks separate allows:
- Independent deploy/rollback of agent vs. API
- Clear ownership boundary (agentcore CLI owns agent infra)
- Simpler rollback: destroy agent stack without touching Lapwise API

### Decision 6: Analysis endpoints are FastAPI routes, not Lambda extensions

The 8 analysis endpoints aggregate data already available via existing Lapwise routes (e.g., laps, stints, pit). They are implemented as new FastAPI route handlers in the `service/` directory, reusing existing OpenF1 client wrapper code. They are NOT separate Lambda functions — the existing Lambda deployment pattern handles them automatically.

**`include_circuit_history` parameter**: Each analysis endpoint accepts an optional `include_circuit_history: bool = False` query param. When true, the endpoint fetches data for the same circuit from the previous 2 years in addition to the requested year — enabling the agent's historical reasoning capability.

### Decision 7: Fantasy prices endpoint is hardcoded JSON

`GET /v1/fantasy/prices` returns a static Python dict (2025 season prices) serialized as JSON. Prices change at the start of each season or after major mid-season price resets. A database or external source is not warranted for a static dataset; the file is updated manually each season. This is the simplest correct approach.

### Decision 8: Agent build type is CodeZip

`agentcore.json` sets `build.type = "CodeZip"` (zip artifact deployed to Lambda). Container image was considered but CodeZip has faster deploy cycles for a Python function of this size and complexity.

## Risks / Trade-offs

**[Risk] GoogleADK has no native AgentCore memory integration** → Mitigation: BYO MemoryClient pattern (Decision 2). Documented pattern — risk is implementation complexity, not feasibility.

**[Risk] Memory not available during `agentcore dev`** → Mitigation: All memory code paths guarded by `if memory_id is None: return` before any MemoryClient calls. Agent works fully without memory in dev mode; memory is a session enhancement not a hard dependency.

**[Risk] Gateway URL not available locally** → Mitigation: Agent loads tools from gateway URL at startup; when `AGENTCORE_GATEWAY_*_URL` is None, agent falls back to no-op tool stubs or skips gateway tool registration. Local dev can invoke tools directly via mocked functions.

**[Risk] OpenAPI target keeps tool catalog in sync, but spec changes could break tool calls** → Mitigation: Any breaking change to Lapwise FastAPI route signatures should be coordinated with a gateway re-registration (`agentcore gateway update`). The semantic search layer absorbs minor parameter renames.

**[Risk] Claude Sonnet 4.5 cross-region inference adds ~50-100ms latency per turn** → Mitigation: Acceptable for a conversational agent. Not a streaming use case. No mitigation needed.

**[Risk] 365-day memory expiry accumulates stale preferences** → Mitigation: Agent exposes `clear_my_preferences()` as a function tool so users can reset. Stale data is low-risk (fantasy preferences, not financial data).

**[Risk] Two Cognito M2M clients require manual rotation coordination** → Mitigation: Each client is rotated independently. Client A rotation does not affect Gateway→Lapwise auth. Document rotation runbook in agent README.

**[Trade-off] agentcore CDK stack separation means two separate `cdk deploy` invocations** → Accepted. Operational simplicity outweighs the slight inconvenience.

## Migration Plan

1. **Add analysis + pricing routes** to Lapwise FastAPI service; deploy via existing CI/CD
2. **Verify `/openapi.json`** is accessible and reflects new routes
3. **Create two Cognito M2M app clients** (A and B) in existing Cognito User Pool; store credentials in AWS Secrets Manager
4. **Configure AgentCore Gateway** via `agentcore gateway create --type open-api-schema --spec-url <url>` with CUSTOM_JWT inbound auth and Cognito outbound auth
5. **Configure AgentCore Memory** via `agentcore memory create` with SUMMARIZATION + USER_PREFERENCE strategies
6. **Configure AgentCore Observability** via `agentcore observability create` with CloudWatch + X-Ray
7. **Create `agent/` directory**, implement `main.py` with GoogleADK agent, wire MemoryClient
8. **Create `agentcore/agentcore.json`** referencing gateway, memory, observability ARNs
9. **Run `agentcore dev`** — smoke test without memory
10. **Run `agentcore deploy`** — deploy to AWS; smoke test with memory
11. **Rollback**: `agentcore destroy` removes agent stack; Lapwise API and infra/ stack are untouched

## Open Questions

- Should the agent support streaming responses (SSE) or is request/response sufficient for v1? (Assumed: request/response for now)
- What Cognito User Pool should M2M clients A and B be created in — the existing Lapwise user pool or a separate service pool? (Assumed: existing user pool for simplicity)
- Should `agentcore dev` mock gateway tools from a local FastAPI instance? (Assumed: no — dev mode tests orchestration logic only; full tool integration tested post-deploy)
- Are the 8 analysis endpoints expected to be synchronous (compute inline) or async (queue + poll)? (Assumed: synchronous — data volumes are small enough for sub-second response)

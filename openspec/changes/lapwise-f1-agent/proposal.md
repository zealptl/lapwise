## Why

Lapwise has a rich F1 data API but no intelligent layer on top of it — users must manually query endpoints and interpret raw data to make F1 Fantasy decisions. This change introduces a generative AI agent that combines historical race data, circuit profiles, and real-time pricing to produce informed, data-backed F1 Fantasy team recommendations, transforming Lapwise from a data API into a decision-support product.

## What Changes

- **New `agent/` directory** alongside `service/` and `infra/` — a standalone GoogleADK + BedrockAgentCore project (`LapwiseF1Agent`) that is deployed independently via `agentcore deploy`
- **New AgentCore Gateway** configured with an OpenAPI target pointing at Lapwise's `/openapi.json`, exposing all Lapwise routes (existing 13 + 8 new analysis endpoints + 1 pricing endpoint) as agent tools
- **New AgentCore Memory resource** with two extraction strategies (SUMMARIZATION for short-term session context, USER_PREFERENCE for long-term fantasy preferences) with 365-day expiry
- **New Cognito M2M app clients** (two separate clients): one for Agent→Gateway auth, one for Gateway→Lapwise API auth — both using client credentials grant
- **New analysis endpoints** (`/v1/analysis/*`) added to the Lapwise FastAPI service: driver pace profile, DNF rates, fastest-lap candidates, overtake profile, circuit profile, championship context, qualifying trends, constructor pitstop
- **New static pricing endpoint** (`/v1/fantasy/prices`) returning hardcoded 2025 F1 Fantasy driver and constructor prices
- **New AgentCore Observability** configuration: CloudWatch + X-Ray tracing at session, tool call, and memory operation levels
- All new infrastructure is managed by the `agentcore` CLI CDK stack — separate from the existing Lapwise `infra/` CDK stack

## Capabilities

### New Capabilities

- `agent-core`: The LapwiseF1Agent GoogleADK application — system prompt, tool wiring, memory integration (BYO MemoryClient pattern), session management, and collaborative recommendation behavior
- `agent-memory`: AgentCore Memory resource configuration — SUMMARIZATION + USER_PREFERENCE strategies, 365-day expiry, userId from Cognito JWT `sub` claim, UUID v4 session IDs, graceful degradation when MEMORY_ID is None
- `agent-gateway`: AgentCore Gateway setup — CUSTOM_JWT inbound auth (M2M client A), Cognito client credentials outbound auth (M2M client B), OpenAPI target pointing at Lapwise `/openapi.json`, semantic search enabled
- `agent-auth`: Two Cognito M2M app clients — client A for Agent→Gateway, client B for Gateway→Lapwise; both using OAuth 2.0 client credentials grant
- `agent-observability`: CloudWatch + X-Ray observability wired through AgentCore Observability service — full traces at session, tool, and memory levels
- `endpoint-analysis`: Eight new FastAPI analysis endpoints under `/v1/analysis/` — driver-pace-profile, dnf-rates, fastest-lap-candidates, overtake-profile, circuit-profile, championship-context, qualifying-trends, constructor-pitstop
- `endpoint-fantasy-prices`: Static `/v1/fantasy/prices` endpoint returning hardcoded 2025 F1 Fantasy driver and constructor prices (JSON)

### Modified Capabilities

- `app-foundation`: AgentCore Gateway requires the Lapwise FastAPI OpenAPI spec to be publicly accessible at `/openapi.json` — confirming the existing FastAPI route is present and the API Gateway + Lambda configuration allows unauthenticated access to that path

## Impact

- **New directory**: `agent/` with `agentcore/agentcore.json` and `app/LapwiseF1Agent/main.py`
- **Lapwise FastAPI service**: 9 new routes added (`/v1/analysis/*` × 8, `/v1/fantasy/prices` × 1)
- **AWS resources** (managed by agentcore CDK): Lambda function, AgentCore Agent runtime, AgentCore Gateway, AgentCore Memory resource, AgentCore Observability, IAM roles, CloudWatch log groups, X-Ray tracing
- **Cognito**: Two new M2M app clients added to existing Cognito User Pool
- **Dependencies**: `bedrock-agentcore`, `bedrock-agentcore-starter-toolkit`, `google-adk`, `boto3` (for MemoryClient) added to agent project
- **No changes** to existing CDK `infra/` stack, existing FastAPI routes, or existing Cognito user-facing app clients

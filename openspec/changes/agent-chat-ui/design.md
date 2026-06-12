# Design — Agent Chat UI

## Context

LapwiseF1Agent runs on BedrockAgentCore with CUSTOM_JWT inbound auth against the Lapwise Cognito User Pool (`us-east-1_Q1p1bedp6`, allowed audience = the `LapwiseAppClient` client id). The runtime entrypoint accepts `{"message", "session_id", "user_id"}` and returns `{"response", "session_id"}` (non-streaming). The agent persists turns to AgentCore Memory (`LapwiseF1Agent_LapwiseMemory-BpEoUO9hnK`) via `MemoryClient.create_event` with plain `(text, USER|ASSISTANT)` message tuples — i.e. standard conversational event payloads, not framework-specific blobs.

The existing `infra/` stack has an HTTP API with a Cognito JWT default authorizer routing everything to the Lapwise FastAPI Lambda. The User Pool currently has `selfSignUpEnabled: false` and the app client only enables `userPassword` auth flow. There is no frontend.

## Goals / Non-Goals

**Goals:**
- A locally-run React SPA where a user signs up / signs in with Cognito and chats with the agent.
- Conversation lifecycle: new session, switch sessions, reload full history of past conversations.
- A distinctive dark F1 telemetry aesthetic — explicitly not a generic AI chat skin.
- Minimal new backend surface: one small Lambda for conversation listing/replay.

**Non-Goals:**
- Hosting/deployment of the SPA (S3/CloudFront deferred to a later change).
- Streaming agent responses (the agent entrypoint is request/response today).
- Agent code changes, MFA, social sign-in, password reset flows beyond Cognito's basic forgot-password.
- Conversation deletion/search.

## Decisions

### 1. Browser → AgentCore directly with the user's Cognito JWT
The SPA calls `InvokeAgentRuntime` over HTTPS: `POST https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{urlencoded runtime ARN}/invocations?qualifier=DEFAULT` with `Authorization: Bearer <token>` and `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` (33+ chars; `crypto.randomUUID()` is 36). Body matches the agent's contract: `{"message", "session_id", "user_id"}` where `user_id` = Cognito `sub` and `session_id` = the same UUID used in the header.

- *Why not a proxy?* The runtime already validates this pool/client's JWTs; a proxy adds infra and latency for no gain. (Fallback exists — see Risks.)
- *Token choice:* the runtime's `customJwtAuthorizer` is configured with `allowedAudience`, which validates the `aud` claim. Cognito **ID tokens** carry `aud`; access tokens carry `client_id` instead. So the SPA sends the **ID token** to AgentCore and the **access token** to the Lapwise HTTP API. If ID-token auth fails in practice, switch the runtime config to `allowedClients` (validates `client_id`) and send the access token everywhere — verify during implementation.

### 2. Conversation list in DynamoDB; replay from AgentCore Memory
Following the agreed pattern: a DynamoDB table (`actor_id` PK, `session_id` SK, attrs `conversation_name`, `created_at`) is the source of truth for "my conversations"; AgentCore Memory `list_events` is the source of truth for messages. The frontend `PUT`s metadata when the first user message of a new session is sent (name = first message truncated to ~60 chars).

- *Decode divergence from the reference example:* the reference decodes LangGraph msgpack checkpoint blobs. This agent writes conversational tuples via `MemoryClient.create_event`, so `list_events` returns `payload[].conversational.{content.text, role}` — the messages endpoint maps those directly (role `USER`→`user`, `ASSISTANT`→`assistant`, sorted by `eventTimestamp`). No msgpack needed.
- *Why not Memory alone?* No efficient "list sessions for actor with titles" API; DynamoDB gives a cheap, ordered sidebar query.
- *Why not DynamoDB alone?* Messages are already persisted by the agent's memory callback; duplicating them client-side risks drift.

### 3. Conversations API: a new small Lambda on the existing HTTP API
A Python 3.12 Lambda (boto3 only, managed with uv) registered on explicit routes, behind the existing Cognito JWT default authorizer:

- `GET /v1/conversations` — Query DynamoDB by actor, newest first.
- `PUT /v1/conversations/{sessionId}` — upsert `{conversation_name}` metadata.
- `GET /v1/conversations/{sessionId}/messages` — `list_events` replay.

`actor_id` is **always** read from the JWT `sub` in `event.requestContext.authorizer.jwt.claims` — never from the request — so users can only see their own conversations. IAM scoped to `dynamodb:Query/PutItem` on the table and `bedrock-agentcore:ListEvents` on the memory resource.

- *Why not extend the FastAPI service?* The data API would need bedrock-agentcore/DynamoDB permissions and its OpenAPI schema feeds the AgentCore Gateway tool catalog — conversation routes would leak into the agent's toolset. A separate Lambda keeps blast radius and IAM tight.

### 4. Cognito: custom forms via `amazon-cognito-identity-js`, SRP
Custom signup/signin pages using SRP (`userSrp: true` added to the app client; `selfSignUpEnabled: true` + email auto-verification on the pool). Signup → email verification code → signin. The library handles token caching/refresh in localStorage by default — acceptable for this app; no Hosted UI redirect breaks the visual experience.

- *Why not aws-amplify?* Full Amplify pulls in far more than needed; `amazon-cognito-identity-js` is the same underlying auth implementation, standalone.

### 5. Frontend stack and design direction
Vite + React + TypeScript + Tailwind + shadcn/ui, React Router (routes: `/signin`, `/signup`, `/verify`, `/` chat shell), `react-markdown` for agent responses. **Implementation MUST use the `frontend-design:frontend-design` skill.**

Design direction (dark F1 telemetry — to be refined by the skill at build time):
- Carbon/near-black layered surfaces, a single racing accent (red/amber), thin luminous dividers evoking timing screens.
- Conversation sidebar styled as a timing tower (position-style rows, monospace timestamps).
- Condensed grotesque display type + monospace for data; chat bubbles avoided in favor of full-width "stint" blocks separated by sector lines.
- Loading state as a sector-time/telemetry pulse, not a generic spinner or three dots.
- The agent's three-scenario output (Best team / Value picks / Risk-tolerant) rendered with distinct visual treatment per scenario.

### 6. CORS
The HTTP API gets `corsPreflight` for `http://localhost:5173` (GET/PUT/OPTIONS, `Authorization` + `Content-Type` headers). AgentCore's data plane CORS is verified during implementation (see Risks).

## Risks / Trade-offs

- [AgentCore data plane may not return CORS headers for browser calls] → Verify early (task 1). Fallback: add `POST /v1/agent/invoke` to the conversations Lambda, which forwards to `InvokeAgentRuntime` server-side; frontend swaps one base URL.
- [`allowedAudience` vs token type mismatch (ID vs access token)] → Test both tokens against the runtime in task 1; switch runtime config to `allowedClients` if needed (one-line `agentcore.json` change + redeploy).
- [Self-signup opens public registration] → Email verification required; acceptable for this stage. Rate limiting/WAF deferred.
- [Tokens in localStorage are XSS-readable] → Accepted trade-off for a local dev SPA; no third-party scripts; revisit before public hosting.
- [Agent responses can take 30s+ (tool calls)] → Generous fetch timeout (120s), rich telemetry-style progress state, disable composer while in flight.
- [Memory persistence is the agent's after-callback; replay may lag the live session] → The UI keeps the live session transcript in client state; Memory replay is only used when loading a *past* conversation.
- [User pool property changes (`selfSignUpEnabled`) update in place] → No replacement risk; verified CloudFormation update behavior for `AWS::Cognito::UserPool`.

## Open Questions

- None blocking. Token-type (ID vs access) and AgentCore CORS are verified as the first implementation task with explicit fallbacks above.

# Tasks — Agent Chat UI

## 1. Verify auth assumptions (de-risk first)

- [ ] 1.1 Obtain Cognito tokens for a test user (USER_PASSWORD_AUTH via aws cli) and call `InvokeAgentRuntime` over HTTPS with the ID token, then the access token; record which is accepted by the runtime's `allowedAudience` config
- [ ] 1.2 Check whether the AgentCore data plane returns CORS headers for a browser-origin preflight; if not, note the proxy fallback (`POST /v1/agent/invoke`) as required and add it to scope
- [ ] 1.3 If the ID token is rejected, switch `agentcore.json` to `allowedClients` and redeploy the agent

## 2. Infra (CDK)

- [ ] 2.1 Update `infra/lib/lapwise-stack.ts`: User Pool `selfSignUpEnabled: true` with email auto-verify; app client adds `userSrp: true`
- [ ] 2.2 Add DynamoDB conversations table (PK `actor_id`, SK `session_id`, on-demand billing)
- [ ] 2.3 Add conversations Lambda (Python 3.12) with scoped IAM (table Query/PutItem, `bedrock-agentcore:ListEvents` on the memory resource) and env vars `CONVERSATION_TABLE`, `AGENTCORE_MEMORY_ID`
- [ ] 2.4 Register routes `GET /v1/conversations`, `PUT /v1/conversations/{sessionId}`, `GET /v1/conversations/{sessionId}/messages` on the HTTP API under the existing JWT authorizer
- [ ] 2.5 Add `corsPreflight` for `http://localhost:5173` (GET/PUT/OPTIONS, Authorization + Content-Type)
- [ ] 2.6 If task 1.2 demanded it, add `POST /v1/agent/invoke` proxy route with `bedrock-agentcore:InvokeAgentRuntime` permission
- [ ] 2.7 Deploy and verify stack outputs (table name, routes live)

## 3. Conversations Lambda

- [ ] 3.1 Implement handler with route dispatch; derive `actor_id` from `requestContext.authorizer.jwt.claims.sub` only
- [ ] 3.2 Implement list (DynamoDB Query, newest first) and upsert (PutItem with name truncation server-side as defense-in-depth)
- [ ] 3.3 Implement message replay: `list_events` → map `payload[].conversational` to `{role, content, timestamp}`, sorted chronologically
- [ ] 3.4 Unit tests for route dispatch, actor isolation, and conversational payload mapping (use uv, not pip)
- [ ] 3.5 Integration check: chat once via `agentcore invoke`, then confirm the session replays through the deployed endpoint

## 4. Web app foundation

- [ ] 4.1 Scaffold `web/` with Vite + React + TypeScript, Tailwind, shadcn/ui, React Router, react-markdown, amazon-cognito-identity-js; add `.env.example` and config module with missing-var error screen
- [ ] 4.2 **Invoke the `frontend-design:frontend-design` skill** and establish the F1 telemetry design system per design.md (tokens, typography, surfaces, motion, loading treatments) — no generic AI chat tropes
- [ ] 4.3 Build the routing shell with auth guard (protected `/`, public `/signin` `/signup` `/verify`, redirects both directions)

## 5. Auth pages

- [ ] 5.1 Auth service module: signup, confirm, resend code, SRP signin, session refresh, signout; ID token → AgentCore, access token → Lapwise API
- [ ] 5.2 Signin page with inline Cognito error mapping and unconfirmed-user redirect to `/verify`
- [ ] 5.3 Signup page with field-level validation against the pool's password policy
- [ ] 5.4 Verification page with code entry + resend; route to chat on success
- [ ] 5.5 Manual E2E: fresh email signs up, verifies, signs in, lands on chat; signout returns to signin with state cleared

## 6. Chat experience

- [ ] 6.1 Agent client: `InvokeAgentRuntime` fetch wrapper (URL-encoded runtime ARN, session header, 120s tolerance, typed errors)
- [ ] 6.2 Chat state: session id lifecycle (new UUID per conversation), transcript state, send/retry actions
- [ ] 6.3 Transcript UI: full-width turn blocks per design system, markdown rendering with distinct three-scenario treatment
- [ ] 6.4 Composer: multi-line, Enter/Shift+Enter, disabled in flight, focus management
- [ ] 6.5 Telemetry-styled in-flight indicator and inline retryable error states

## 7. Conversation history UI

- [ ] 7.1 Conversations API client (list, upsert, messages) using the access token
- [ ] 7.2 Sidebar: timing-tower conversation list, active highlight, new-conversation control
- [ ] 7.3 Auto-register conversation on first message (name = first message ≤60 chars)
- [ ] 7.4 Load past conversation: replay messages into transcript, resume session id for new turns

## 8. Verification & polish

- [ ] 8.1 Full E2E pass: signup → verify → signin → new chat → multi-turn (context retained) → second conversation → switch back and resume the first → signout
- [ ] 8.2 Design QA against spec: no generic spinners/bubbles/typing dots; consistent tokens on every page; long-response (60s+) behavior
- [ ] 8.3 `npm run build` clean; Lambda tests green; update root/web READMEs with setup + env vars

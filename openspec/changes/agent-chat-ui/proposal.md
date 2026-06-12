# Agent Chat UI

## Why

LapwiseF1Agent is deployed and answerable only via `agentcore invoke` or raw `InvokeAgentRuntime` calls — there is no way for a real user to sign up, sign in, and chat with the agent. A web UI is needed so users can converse with the F1 Fantasy advisor, revisit previous conversations, and start fresh sessions, with Cognito handling identity end to end.

## What Changes

- New `web/` directory: a React + Vite + Tailwind + shadcn/ui single-page app with a dark, motorsport/telemetry-inspired design (no generic AI chat aesthetic). Run locally via `npm run dev`; hosting is deferred to a later change.
- Custom Cognito signup and signin pages (email + password, email verification code flow) using the existing Lapwise User Pool app client — no Hosted UI.
- Chat screen that calls the AgentCore runtime (`InvokeAgentRuntime`) directly from the browser with the user's Cognito access token (the runtime already has CUSTOM_JWT inbound auth against this pool/client).
- Conversation management: start a new session, switch between sessions, and reload full message history of previous conversations.
- New conversations API: two JWT-authorized routes on the existing Lapwise HTTP API backed by a new Lambda — `GET /v1/conversations` (list from a new DynamoDB metadata table) and `GET /v1/conversations/{sessionId}/messages` (replay from AgentCore Memory `list_events`).
- New DynamoDB table storing conversation metadata (`actor_id`, `session_id`, `conversation_name`, `created_at`), written via `PUT /v1/conversations/{sessionId}` when the frontend starts a new conversation.
- Infra changes in `infra/lib/lapwise-stack.ts`: enable Cognito self-signup, enable SRP auth flow on the app client, add the conversations Lambda + routes + DynamoDB table, and add CORS configuration for the local dev origin.

## Capabilities

### New Capabilities

- `web-foundation`: SPA scaffold, routing, auth-aware shell, environment configuration, and the F1 telemetry design system (typography, palette, motion).
- `web-auth`: signup, email verification, signin, signout, and token/session management against the Lapwise Cognito User Pool.
- `web-chat`: the chat experience — composing messages, invoking the agent with the user's JWT, rendering structured three-scenario responses, loading states, and error handling.
- `conversation-history`: listing, naming, creating, and reloading conversations — covers the DynamoDB metadata table, the conversations API routes, and the sidebar UI that consumes them.

### Modified Capabilities

<!-- none: the Cognito user pool and HTTP API exist in infra but have no spec in openspec/specs/; their config changes (self-signup, SRP flow, CORS, new routes) are captured inside the new capabilities above -->

## Impact

- **New code**: `web/` (React SPA), `service/` untouched; new Lambda for conversations API (location decided in design).
- **Infra**: `infra/lib/lapwise-stack.ts` — User Pool (`selfSignUpEnabled: true`), app client auth flows (`userSrp: true`), new DynamoDB table, new Lambda + HTTP API routes, CORS.
- **Security**: self-signup opens the user pool to public registration; signups gated by email verification. Browser holds Cognito tokens (access + refresh) — stored in memory/localStorage per design.
- **Agent**: no code changes to `agent/` — the existing `{message, session_id, user_id}` payload contract and Memory event format are consumed as-is.
- **Dependencies**: frontend adds `react`, `vite`, `tailwindcss`, `shadcn/ui`, `amazon-cognito-identity-js` (or `aws-amplify` auth category), `react-router`, `react-markdown`.

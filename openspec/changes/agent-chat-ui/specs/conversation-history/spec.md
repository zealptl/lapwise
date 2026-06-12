# conversation-history

## ADDED Requirements

### Requirement: Conversation metadata table
The infra SHALL provision a DynamoDB table for conversation metadata with partition key `actor_id` (Cognito sub) and sort key `session_id`, storing `conversation_name` and `created_at` (ISO 8601), billed on-demand.

#### Scenario: Table provisioned by CDK
- **WHEN** the updated `infra/` stack is deployed
- **THEN** the conversations table exists with the specified key schema and on-demand billing

### Requirement: Conversations API routes
The system SHALL expose three JWT-authorized routes on the existing Lapwise HTTP API, served by a dedicated Lambda: `GET /v1/conversations` (list, newest first), `PUT /v1/conversations/{sessionId}` (upsert `conversation_name` metadata), and `GET /v1/conversations/{sessionId}/messages` (ordered message replay). The Lambda SHALL derive `actor_id` exclusively from the JWT `sub` claim in the request context — never from client-supplied parameters — and its IAM role SHALL be scoped to Query/PutItem on the table and ListEvents on the memory resource. The HTTP API SHALL allow CORS from the local dev origin for these routes.

#### Scenario: List own conversations only
- **WHEN** an authenticated user calls `GET /v1/conversations`
- **THEN** only conversations whose `actor_id` equals their JWT `sub` are returned, ordered most recent first

#### Scenario: Cross-user access is impossible
- **WHEN** a user requests messages for a `sessionId` belonging to another user
- **THEN** the API queries Memory with the caller's own `sub` as actor id and returns an empty message list, never another user's data

#### Scenario: Browser preflight succeeds
- **WHEN** the SPA at `http://localhost:5173` issues a CORS preflight for a conversations route
- **THEN** the HTTP API responds permitting the origin, `Authorization` header, and GET/PUT methods

### Requirement: Message replay from AgentCore Memory
The messages endpoint SHALL call `list_events` on the AgentCore Memory resource with the caller's actor id and the requested session id, map conversational payloads (`payload[].conversational`) to `{role: user|assistant, content, timestamp}`, and return them sorted by event timestamp.

#### Scenario: Past conversation replays correctly
- **WHEN** messages are requested for a session previously persisted by the agent's memory callback
- **THEN** the full alternating user/assistant transcript is returned in chronological order with roles mapped from `USER`/`ASSISTANT`

### Requirement: Conversation sidebar
The chat shell SHALL display a sidebar (styled per the design system) listing the user's conversations by name and date, with a prominent new-conversation control. Selecting a conversation SHALL load its replayed history into the chat view and resume that `session_id` for subsequent messages; the active conversation SHALL be visually indicated.

#### Scenario: Load a previous conversation
- **WHEN** the user selects a past conversation from the sidebar
- **THEN** its full message history renders in the transcript and new messages are sent with that conversation's session id

#### Scenario: Start a new conversation
- **WHEN** the user activates the new-conversation control
- **THEN** the transcript clears and a fresh session id (new UUID) is generated for the next message

### Requirement: Automatic conversation registration
When the first message of a new session is sent, the app SHALL `PUT /v1/conversations/{sessionId}` with a `conversation_name` derived from that message (truncated to at most 60 characters), so the conversation appears in the sidebar without user action.

#### Scenario: New conversation appears in sidebar
- **WHEN** a user sends the first message of a fresh session
- **THEN** the conversation is registered with a name derived from the message and appears at the top of the sidebar

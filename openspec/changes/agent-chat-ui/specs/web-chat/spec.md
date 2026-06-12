# web-chat

## ADDED Requirements

### Requirement: Agent invocation from the browser
The app SHALL invoke the AgentCore runtime directly via `InvokeAgentRuntime` HTTPS calls using the authenticated user's Cognito JWT as bearer token, sending `{"message", "session_id", "user_id"}` where `user_id` is the Cognito `sub` and `session_id` matches the `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` header (a UUID, satisfying the 33+ character minimum).

#### Scenario: Message round-trip
- **WHEN** an authenticated user sends a message in an active session
- **THEN** the runtime is called with the user's JWT and session id, and the returned `response` text is rendered as a new agent message

#### Scenario: Session affinity preserved across turns
- **WHEN** a user sends multiple messages in one conversation
- **THEN** every invocation uses the same `session_id`, so the agent retains in-session context

### Requirement: Chat transcript rendering
The chat view SHALL render the running transcript with user and agent turns visually distinct per the design system, rendering agent markdown (headings, lists, tables) correctly — including the agent's three-scenario structure (Best team / Value picks / Risk-tolerant) with differentiated visual treatment per scenario.

#### Scenario: Markdown response renders structured
- **WHEN** the agent returns its three-scenario markdown response
- **THEN** each scenario section renders with its distinct styling and no raw markdown syntax is visible

### Requirement: In-flight and error states
While an invocation is in flight the composer SHALL be disabled and a telemetry-styled progress indicator shown, tolerating responses up to 120 seconds. Failed invocations SHALL show an inline error on the affected turn with a retry action that re-sends the same message on the same session.

#### Scenario: Long-running agent call
- **WHEN** the agent takes 60 seconds to respond (tool calls)
- **THEN** the progress indicator remains active and the response renders on arrival without timeout

#### Scenario: Failed invocation is retryable
- **WHEN** an invocation fails (network error or non-2xx)
- **THEN** an inline error appears with a retry control, and retrying re-sends the identical message with the same session id

### Requirement: Message composer
The composer SHALL support multi-line input, submit on Enter (newline on Shift+Enter), reject empty messages, and return focus after each send.

#### Scenario: Keyboard submission
- **WHEN** the user types a message and presses Enter
- **THEN** the message is sent; Shift+Enter inserts a newline instead

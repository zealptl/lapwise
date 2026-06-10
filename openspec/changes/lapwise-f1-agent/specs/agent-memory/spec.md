## ADDED Requirements

### Requirement: Memory resource has two extraction strategies with 365-day expiry
The AgentCore Memory resource SHALL be configured with two strategies:
1. `SUMMARIZATION` — for short-term session context (conversation summary)
2. `USER_PREFERENCE` — for long-term fantasy preferences

Both strategies SHALL have an expiry of 365 days. Both passive extraction (automatic at session end) and explicit saving (agent-triggered `@function_tool`) SHALL be enabled for USER_PREFERENCE.

#### Scenario: Memory resource is created with correct strategies
- **WHEN** the AgentCore Memory resource is provisioned
- **THEN** it SHALL have exactly two strategies: SUMMARIZATION and USER_PREFERENCE, each with 365-day expiry

### Requirement: userId is extracted from Cognito JWT sub claim
The agent SHALL NOT pass `userId` explicitly. AgentCore SHALL automatically extract the `userId` from the `sub` claim of the inbound Cognito JWT.

#### Scenario: userId is not passed in agent code
- **WHEN** MemoryClient calls are made during a session
- **THEN** no explicit `userId` parameter is set in agent code — AgentCore derives it from the token

### Requirement: Session IDs are UUID v4 with minimum 33 characters
Session IDs passed to AgentCore memory operations SHALL be UUID v4 strings. UUID v4 is always ≥36 characters, satisfying AgentCore's minimum 33-character requirement for LTM extraction.

#### Scenario: Session ID format is valid
- **WHEN** a new conversation session is started
- **THEN** the session ID SHALL be a UUID v4 string (e.g., `"550e8400-e29b-41d4-a716-446655440000"`) with length ≥ 33

#### Scenario: Caller-provided session ID is used
- **WHEN** the request body contains a `session_id` field
- **THEN** the agent SHALL use that value as the session ID for memory operations

#### Scenario: Session ID is auto-generated when absent
- **WHEN** the request body does not contain a `session_id` field
- **THEN** the agent SHALL generate a UUID v4 session ID automatically

### Requirement: Memory is loaded at session start
At the beginning of each session, the agent SHALL call `MemoryClient.retrieve()` to load:
1. The conversation summary (SUMMARIZATION strategy) for the current user
2. The user's stored preferences (USER_PREFERENCE strategy) for the current user

Both results SHALL be injected into the agent's system prompt context for that session.

#### Scenario: Conversation summary is injected into context
- **WHEN** a user returns to an existing session
- **THEN** the agent's context SHALL include a summary of prior conversation turns (Human + AI only, no internal tool call internals)

#### Scenario: User preferences are injected into context
- **WHEN** a user starts a session and has stored preferences
- **THEN** the agent's context SHALL include their preferences (e.g., favorite driver, budget style, circuit preference, constructor bias, fantasy platform)

### Requirement: Memory operations are skipped when MEMORY_ID is None
All MemoryClient calls SHALL be guarded by a check: if `MEMORY_ID` environment variable is `None` or not set, skip the memory operation and continue without error.

#### Scenario: Agent runs without memory in local dev
- **WHEN** `MEMORY_ID` is not set (e.g., `agentcore dev`)
- **THEN** agent SHALL start and respond to requests without any MemoryClient calls, and SHALL NOT raise an exception

### Requirement: Agent saves explicit preferences via function tool
The agent SHALL expose a `save_user_preference` `@function_tool`. When the user directly states a preference (e.g., "I always play on the Official F1 Fantasy app" or "I prefer budget-focused teams"), the agent SHALL call this tool and confirm: "Got it, I'll remember that."

#### Scenario: Explicit preference is saved and confirmed
- **WHEN** user says "I always pick Max Verstappen"
- **THEN** agent SHALL call `save_user_preference` with the preference and respond confirming it will be remembered

#### Scenario: Passive preference extraction occurs at session end
- **WHEN** a session ends
- **THEN** AgentCore's USER_PREFERENCE strategy SHALL automatically extract any inferred preferences from the conversation without agent code intervention

### Requirement: Memory stores fantasy-relevant preference fields
The USER_PREFERENCE strategy SHALL store: favorite drivers, budget style, circuit preferences, constructor bias, and fantasy platform.

#### Scenario: Budget style preference is persisted across sessions
- **WHEN** user states "I prefer value picks under £10M" in session 1
- **THEN** in session 2, the agent's context SHALL include this budget style preference

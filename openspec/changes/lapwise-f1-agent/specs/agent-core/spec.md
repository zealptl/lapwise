## ADDED Requirements

### Requirement: Agent project structure exists
The `agent/` directory SHALL exist at the repo root alongside `service/` and `infra/`, containing `agentcore/agentcore.json` and `app/LapwiseF1Agent/main.py`.

#### Scenario: Directory layout is correct
- **WHEN** a developer clones the repo
- **THEN** the paths `agent/agentcore/agentcore.json` and `agent/app/LapwiseF1Agent/main.py` SHALL exist

### Requirement: Agent uses GoogleADK with BedrockAgentCoreApp runtime
The agent SHALL be implemented using the GoogleADK framework and wrapped with `BedrockAgentCoreApp` from `bedrock_agentcore.runtime` for deployment on AWS BedrockAgentCore.

#### Scenario: Agent starts without errors
- **WHEN** `BedrockAgentCoreApp` wraps the GoogleADK agent and the app is invoked
- **THEN** the agent initializes without import errors and is ready to handle requests

### Requirement: Agent uses Claude Sonnet 4.5 via Bedrock cross-region inference
The agent SHALL use the model ID `global.anthropic.claude-sonnet-4-5-20250929-v1:0` via Bedrock in region `us-east-1`.

#### Scenario: Correct model is configured
- **WHEN** the agent is initialized
- **THEN** the model ID in `agentcore.json` and in the GoogleADK agent configuration SHALL both be `global.anthropic.claude-sonnet-4-5-20250929-v1:0`

### Requirement: Agent has a collaborative system prompt
The agent's system prompt SHALL instruct it to:
- Ask clarifying questions before recommending (e.g., remaining budget, drivers already owned)
- Produce three scenarios: best team, value play, and risk-tolerant pick
- Include a boost recommendation (which driver to double)
- Reason from historical data and be transparent about it ("Based on historical data...")
- Never refuse to answer pre-race — always use historical analysis
- Apply the official F1 Fantasy scoring rules (DNF avoidance highest priority, then positions gained, constructor pitstop speed, fastest lap, overtakes, qualifying position, boost allocation)
- Be aware of chips: Autopilot, x3 Boost, No Negative, Wildcard, Limitless, Final Fix

#### Scenario: Agent asks clarifying questions before recommending
- **WHEN** user asks "What should my Monaco 2026 fantasy team be?"
- **THEN** agent SHALL ask at least one clarifying question (e.g., remaining budget or locked drivers) before producing a recommendation

#### Scenario: Agent produces three scenarios
- **WHEN** agent has sufficient context to recommend
- **THEN** response SHALL include best team, value play, and risk-tolerant scenarios plus a boost pick

#### Scenario: Agent is transparent about historical data
- **WHEN** agent references historical race results in its reasoning
- **THEN** response SHALL explicitly state it is using historical data

### Requirement: Agent tool registration uses AgentCore Gateway
The agent SHALL register tools from the AgentCore Gateway URL at startup. When `AGENTCORE_GATEWAY_ENDPOINT_URL` environment variable is not set or is `None`, the agent SHALL skip gateway tool registration and log a warning.

#### Scenario: Tools registered from gateway in production
- **WHEN** `AGENTCORE_GATEWAY_ENDPOINT_URL` is set
- **THEN** agent SHALL register all tools exposed by the gateway

#### Scenario: Graceful degradation when gateway URL is absent
- **WHEN** `AGENTCORE_GATEWAY_ENDPOINT_URL` is not set (local dev)
- **THEN** agent SHALL start without error and log a warning that gateway tools are unavailable

### Requirement: Agent build type is CodeZip
`agentcore.json` SHALL set `build.type` to `"CodeZip"` so the agent is packaged as a zip artifact for Lambda deployment.

#### Scenario: agentcore deploy produces a zip artifact
- **WHEN** `agentcore deploy` is run
- **THEN** the agent is packaged and deployed as a zip-based Lambda function without container image build

### Requirement: agentcore.json references memory, gateway, and observability
`agentcore.json` SHALL include ARN or resource ID references for: the AgentCore Memory resource, the AgentCore Gateway, and the AgentCore Observability configuration.

#### Scenario: All resource references are present
- **WHEN** `agentcore.json` is read
- **THEN** it SHALL contain non-empty values for memory resource ID, gateway ID, and observability resource ID

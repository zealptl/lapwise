## ADDED Requirements

### Requirement: AgentCore Observability is provisioned with CloudWatch and X-Ray
An AgentCore Observability resource SHALL be created and configured to emit traces to:
- **CloudWatch Logs**: Full session-level and tool-call-level structured logs
- **AWS X-Ray**: Distributed traces spanning agent → gateway → Lapwise API

#### Scenario: Observability resource is created
- **WHEN** `agentcore observability create` is run
- **THEN** a new AgentCore Observability resource SHALL exist and be referenced in `agentcore.json`

#### Scenario: CloudWatch log group exists after deploy
- **WHEN** `agentcore deploy` completes
- **THEN** a CloudWatch log group for `LapwiseF1Agent` SHALL exist in the `us-east-1` region

### Requirement: Traces are captured at session level
Each agent session SHALL produce a root trace in X-Ray that spans the full duration of the session from first user message to final response.

#### Scenario: Session produces a root X-Ray trace
- **WHEN** a user sends a message to the agent
- **THEN** X-Ray SHALL record a root segment for that session invocation with session ID as a trace annotation

### Requirement: Traces are captured at tool-call level
Each invocation of an agent tool (i.e., call to a Lapwise API endpoint via the gateway) SHALL produce a child span within the session trace.

#### Scenario: Tool call appears as child span
- **WHEN** agent calls `GET /v1/analysis/dnf-rates` via the gateway
- **THEN** X-Ray SHALL record a child segment labeled with the tool name and response latency

### Requirement: Memory operations are traced
MemoryClient `retrieve` and `store` calls SHALL produce child spans within the session trace.

#### Scenario: Memory retrieve produces a span
- **WHEN** agent calls `MemoryClient.retrieve()` at session start
- **THEN** X-Ray SHALL record a child segment for the memory retrieval with success/failure status

#### Scenario: Memory store produces a span
- **WHEN** agent calls `save_user_preference` function tool
- **THEN** X-Ray SHALL record a child segment for the memory store operation

### Requirement: Observability is provisioned fresh (greenfield)
No pre-existing observability infrastructure exists for the agent. All CloudWatch log groups, X-Ray sampling rules, and AgentCore Observability resources SHALL be created as part of this change.

#### Scenario: No manual pre-provisioning required
- **WHEN** `agentcore deploy` is run for the first time
- **THEN** all required observability resources SHALL be created automatically via the agentcore CDK stack

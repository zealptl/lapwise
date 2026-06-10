# LapwiseF1Agent

An F1 Fantasy advisor built on GoogleADK + AWS BedrockAgentCore. Answers natural-language fantasy questions by calling Lapwise analysis endpoints as tools and returning structured three-scenario recommendations.

## Architecture

```
User (Cognito JWT) → AgentCore runtime (LapwiseF1Agent)
                       ↓ client credentials (M2M client A)
                     AgentCore Gateway (LapwiseGateway)
                       ↓ client credentials (M2M client B)
                     Lapwise API (/v1/analysis/*, /v1/fantasy/prices)
```

Memory: AgentCore Memory resource with SUMMARY (short-term) + USER_PREFERENCE (long-term, 365-day expiry) strategies.

## Local development

```bash
cd agent

# Install dependencies
pip install -r requirements.txt

# Run without AWS (memory and gateway tools disabled)
agentcore dev --port 8080

# Smoke test (in another terminal)
python -m tests.smoke_test
```

In dev mode, `MEMORY_ID` and `AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` are absent. The agent starts without memory or Lapwise tools — useful for testing orchestration logic only.

## Required environment variables

| Variable | Description |
|---|---|
| `MEMORY_ID` | AgentCore Memory resource ID |
| `COGNITO_CLIENT_A_SECRET_ARN` | Secrets Manager ARN for M2M client A secret (not the raw secret) |
| `COGNITO_CLIENT_A_ID` | M2M client A `client_id` |
| `AWS_REGION` | AWS region (default: `us-east-1`) |

`AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL` is injected automatically by `agentcore deploy`.

## Deployment

```bash
# From repo root
cd agent
agentcore deploy

# Verify
agentcore status
```

The `agentcore` CLI manages a separate CDK stack. It does not affect the Lapwise API `infra/` stack.

## Rollback

```bash
cd agent
agentcore destroy
```

This removes the agent Lambda, AgentCore Agent runtime, and associated IAM roles. The Lapwise API (`infra/`) is unaffected.

## M2M client rotation runbook

### Client A (Agent → Gateway)
1. Create a new Cognito app client in the Lapwise User Pool with client credentials grant
2. Update secret in Secrets Manager at `lapwise/agent/cognito-client-a`
3. Set `COGNITO_CLIENT_A_ID` to the new client ID (via `agentcore env set`)
4. The Lambda picks up the new secret on the next cold start (`CognitoTokenCache._load_secret`)
5. Delete the old Cognito app client after verifying traffic has migrated

### Client B (Gateway → Lapwise)
1. Create a new Cognito app client in the Lapwise User Pool with client credentials grant
2. Update secret in Secrets Manager at `lapwise/agent/cognito-client-b`
3. Add the new `client_id` to `LAPWISE_M2M_CLIENT_B_ID` env var and redeploy `infra/` so the JWT authorizer accepts both old and new tokens during rotation
4. Update the AgentCore Gateway outbound auth to use the new client (`agentcore gateway update`)
5. Remove the old `client_id` from `LAPWISE_M2M_CLIENT_B_ID` and redeploy `infra/`

Client A and client B can be rotated independently without affecting the other hop.

## Running tests

```bash
cd agent
pytest tests/
```

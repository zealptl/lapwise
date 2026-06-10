## ADDED Requirements

### Requirement: Two separate Cognito M2M app clients are created
Two distinct Cognito app clients SHALL be created in the existing Lapwise Cognito User Pool:
- **Client A**: Used by the agent to authenticate against the AgentCore Gateway (Agent→Gateway hop)
- **Client B**: Used by the AgentCore Gateway to authenticate against the Lapwise API (Gateway→Lapwise hop)

These clients SHALL NOT be shared or reused across hops.

#### Scenario: Client A and Client B are distinct app clients
- **WHEN** the Cognito User Pool is inspected
- **THEN** there SHALL be two separate app client entries, one identifiable as the agent client (A) and one as the gateway client (B), with different `client_id` values

### Requirement: Both M2M clients use OAuth 2.0 client credentials grant
Both Cognito M2M app clients SHALL be configured to support the OAuth 2.0 `client_credentials` grant type (machine-to-machine, no user interaction).

#### Scenario: Client A issues tokens via client credentials
- **WHEN** the agent POSTs to the Cognito token endpoint with client A's `client_id`, `client_secret`, and `grant_type=client_credentials`
- **THEN** Cognito SHALL return a valid access token

#### Scenario: Client B issues tokens via client credentials
- **WHEN** the AgentCore Gateway POSTs to the Cognito token endpoint with client B's `client_id`, `client_secret`, and `grant_type=client_credentials`
- **THEN** Cognito SHALL return a valid access token accepted by the Lapwise API Gateway authorizer

### Requirement: Client credentials are stored in AWS Secrets Manager
Client A's `client_id` and `client_secret` SHALL be stored as a secret in AWS Secrets Manager. The agent SHALL read these values from environment variables populated from the secret (via agentcore environment configuration), not hardcoded.

#### Scenario: Agent reads credentials from environment variables
- **WHEN** agent code initializes
- **THEN** it SHALL read `COGNITO_CLIENT_A_ID` and `COGNITO_CLIENT_A_SECRET` from environment variables

#### Scenario: Client B credentials are available to gateway
- **WHEN** AgentCore Gateway is configured
- **THEN** Client B's `client_id` and `client_secret` SHALL be provided via the gateway configuration (not in agent code)

### Requirement: Inbound user requests carry Cognito JWTs
Requests from end users to the AgentCore Agent runtime SHALL be authenticated using a Cognito JWT (user identity token with `sub` claim). The `sub` claim is automatically used as `userId` for memory operations.

#### Scenario: Valid user JWT is required to invoke the agent
- **WHEN** a request reaches the AgentCore Agent runtime endpoint
- **THEN** a valid Cognito JWT in the Authorization header SHALL be required; requests without it SHALL be rejected with HTTP 401

#### Scenario: sub claim becomes memory userId
- **WHEN** a user with Cognito `sub` = `"abc-123"` sends a request
- **THEN** all memory read/write operations for that session SHALL be scoped to userId `"abc-123"`

### Requirement: Each hop uses a distinct JWT audience and scope
- Agent→Gateway (client A JWT): audience = AgentCore Gateway resource server
- Gateway→Lapwise (client B JWT): audience = Lapwise API Gateway authorizer

#### Scenario: Client A token is not accepted by Lapwise API directly
- **WHEN** a JWT issued to client A is presented directly to the Lapwise API Gateway authorizer
- **THEN** the Lapwise API SHALL reject it (wrong audience/scope)

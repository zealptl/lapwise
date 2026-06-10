## ADDED Requirements

### Requirement: Cognito User Pool is provisioned for identity management
The CDK stack SHALL provision a Cognito User Pool that manages user accounts and issues JWT tokens for API access.

#### Scenario: User Pool is created with email sign-in
- **WHEN** the stack is deployed
- **THEN** a Cognito User Pool SHALL exist with email as the sign-in identifier

#### Scenario: User Pool Client is created for token issuance
- **WHEN** the stack is deployed
- **THEN** a Cognito User Pool App Client SHALL exist with the USER_PASSWORD_AUTH flow enabled, allowing clients to exchange credentials for tokens

#### Scenario: User Pool ID and Client ID are output after deploy
- **WHEN** `cdk deploy` completes
- **THEN** the Cognito User Pool ID and App Client ID SHALL be printed as CloudFormation stack outputs

### Requirement: API Gateway enforces JWT authorization on all v1 routes
The HTTP API Gateway SHALL attach a JWT authorizer backed by the Cognito User Pool, requiring a valid token on all `/v1/*` routes.

#### Scenario: Authenticated request is forwarded to Lambda
- **WHEN** a request to `/v1/*` includes a valid `Authorization: Bearer <cognito-access-token>` header
- **THEN** API Gateway SHALL validate the token and forward the request to the Lambda function

#### Scenario: Unauthenticated request is rejected
- **WHEN** a request to `/v1/*` is made without an `Authorization` header or with an invalid/expired token
- **THEN** API Gateway SHALL return `401 Unauthorized` and the Lambda SHALL NOT be invoked

#### Scenario: Health check route is exempt from authorization
- **WHEN** a request is made to `/healthz` without any `Authorization` header
- **THEN** API Gateway SHALL forward the request to Lambda and return `{"status": "ok"}` with `200 OK`

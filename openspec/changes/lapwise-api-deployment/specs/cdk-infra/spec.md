## ADDED Requirements

### Requirement: CDK project provisions Lambda and HTTP API Gateway
A TypeScript CDK project SHALL exist at `infra/` and provision a `DockerImageFunction` connected to an HTTP API Gateway v2, producing a public HTTPS endpoint.

#### Scenario: CDK project initializes cleanly
- **WHEN** `npm install` is run in `infra/`
- **THEN** all CDK dependencies resolve and `cdk synth` produces a valid CloudFormation template without errors

#### Scenario: Lambda function is provisioned from container image
- **WHEN** `cdk deploy` runs
- **THEN** a Lambda `DockerImageFunction` SHALL be created using the image built from `service/Dockerfile`, with 512 MB memory and 30 s timeout

#### Scenario: HTTP API Gateway routes all requests to Lambda
- **WHEN** any HTTP request is made to the API Gateway URL
- **THEN** the request SHALL be forwarded to the Lambda via `HttpLambdaIntegration` and the Lambda response returned to the caller

#### Scenario: API Gateway URL is output after deploy
- **WHEN** `cdk deploy` completes successfully
- **THEN** the HTTPS API Gateway URL SHALL be printed as a CloudFormation stack output

### Requirement: CloudWatch log groups are provisioned with retention
The CDK stack SHALL create explicit `LogGroup` resources for both Lambda and API Gateway access logs with a 1-month retention policy.

#### Scenario: Lambda log group has retention set
- **WHEN** the stack is deployed
- **THEN** a CloudWatch log group for Lambda logs SHALL exist with `RetentionDays.ONE_MONTH`

#### Scenario: API Gateway access logs are enabled
- **WHEN** the stack is deployed
- **THEN** the HTTP API default stage SHALL have `accessLogDestination` configured pointing to a dedicated CloudWatch log group, logging structured JSON fields (method, path, status, latency, IP)

#### Scenario: Log groups are not orphaned on stack destroy
- **WHEN** `cdk destroy` is run
- **THEN** the log groups SHALL be removed with the stack (default CDK behavior — no `removalPolicy: RETAIN`)

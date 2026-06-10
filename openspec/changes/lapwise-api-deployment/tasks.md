## 1. Service: Add Mangum dependency and Lambda handler

- [x] 1.1 Add `mangum==22.0.0` to `[project].dependencies` in `service/pyproject.toml`
- [x] 1.2 Run `uv lock` in `service/` to update `uv.lock`
- [x] 1.3 Create `service/src/lapwise/lambda_handler.py` with `handler = Mangum(app, lifespan="off")`

## 2. Service: Add Dockerfile

- [x] 2.1 Create `service/Dockerfile` using `public.ecr.aws/lambda/python:3.12` base image
- [x] 2.2 Install `uv`, copy `pyproject.toml` and `uv.lock`, install dependencies
- [x] 2.3 Copy `src/` and set `CMD ["lapwise.lambda_handler.handler"]`
- [x] 2.4 Verify `docker build` succeeds locally from `service/`

## 3. Infra: Bootstrap TypeScript CDK project

- [x] 3.1 Run `npx cdk init app --language typescript` in `infra/`
- [x] 3.2 Install additional CDK packages: `@aws-cdk/aws-apigatewayv2-alpha`, `@aws-cdk/aws-apigatewayv2-integrations-alpha`
- [x] 3.3 Verify `cdk synth` runs without errors on the scaffolded stack

## 4. Infra: Implement CDK stack

- [x] 4.1 Create `DockerImageFunction` in `lib/lapwise-stack.ts` pointing to `../service` as Docker build context, 512 MB memory, 30 s timeout
- [x] 4.2 Create CloudWatch `LogGroup` for Lambda with `RetentionDays.ONE_MONTH`
- [x] 4.3 Create Cognito `UserPool` with email sign-in and `UserPoolClient` with `USER_PASSWORD_AUTH` flow enabled
- [x] 4.4 Create `HttpApi` with `HttpLambdaIntegration` wiring all routes to the Lambda
- [x] 4.5 Create a `HttpJwtAuthorizer` backed by the Cognito User Pool issuer URL and client ID
- [x] 4.6 Attach the JWT authorizer as the default authorizer on the `HttpApi` (covers all routes)
- [x] 4.7 Add a route override for `GET /healthz` with `authorizationType: HttpNoneAuthorizer` to exempt it from auth
- [x] 4.8 Create CloudWatch `LogGroup` for API Gateway access logs with `RetentionDays.ONE_MONTH`
- [x] 4.9 Enable access logging on the HTTP API default stage with JSON structured format (method, path, status, latency, IP)
- [x] 4.10 Add `CfnOutput` for the API Gateway URL, Cognito User Pool ID, and App Client ID
- [x] 4.11 Run `cdk synth` and confirm CloudFormation template contains Lambda, API Gateway, Cognito User Pool, JWT authorizer, and both log groups

## 5. Deploy and verify

- [x] 5.1 Run `cdk bootstrap` (if not already done for this account/region)
- [x] 5.2 Run `cdk deploy` and confirm it completes without errors
- [x] 5.3 Smoke-test `GET <url>/healthz` without a token → `{"status": "ok"}` (no auth required)
- [x] 5.4 Smoke-test `GET <url>/v1/sessions` without a token → `401 Unauthorized`
- [x] 5.5 Create a test user in Cognito via AWS CLI: `aws cognito-idp admin-create-user` and `admin-set-user-password`
- [x] 5.6 Obtain an access token: `aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH`
- [x] 5.7 Smoke-test `GET <url>/v1/sessions` with `Authorization: Bearer <token>` → returns F1 session data
- [x] 5.8 Verify Lambda logs appear in CloudWatch under `/aws/lambda/lapwise*`
- [x] 5.9 Verify API Gateway access logs appear in the dedicated log group

## Why

Lapwise is a FastAPI wrapper around the OpenF1 public API that currently only runs locally. To make it accessible over the internet with a stable HTTPS endpoint, it needs to be deployed to AWS using Lambda + API Gateway — the lowest-cost, lowest-ops approach for a request-driven API with variable traffic.

## What Changes

- Add `mangum==22.0.0` as a production dependency — the ASGI adapter that lets FastAPI run inside AWS Lambda
- Add a `lambda_handler.py` entry point that wraps the existing FastAPI `app` with Mangum
- Add a `Dockerfile` to package the service as a Lambda container image
- Add a TypeScript CDK project (`infra/`) that provisions all AWS infrastructure

## Capabilities

### New Capabilities

- `lambda-handler`: Mangum-based Lambda entry point wrapping the existing FastAPI app
- `docker-packaging`: Dockerfile that builds the service as a Lambda-compatible container image
- `cdk-infra`: TypeScript CDK stack provisioning Lambda, HTTP API Gateway (v2), and CloudWatch log groups
- `cognito-auth`: Cognito User Pool + JWT authorizer on API Gateway; all API routes require a valid Cognito-issued token

### Modified Capabilities

<!-- No existing spec-level behavior changes — all API routes and responses remain identical -->

## Impact

- **`service/pyproject.toml`**: adds `mangum==22.0.0` dependency
- **`service/src/lapwise/lambda_handler.py`**: new file (Lambda handler)
- **`service/Dockerfile`**: new file (container image build)
- **`infra/`**: new directory (TypeScript CDK project)
- No changes to existing route logic, models, or OpenF1 client behavior
- All API routes (`/v1/*`) require a valid `Authorization: Bearer <token>` header — unauthenticated requests receive 401
- `/healthz` may remain unauthenticated (internal health check)

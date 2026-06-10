## Context

Lapwise is a FastAPI (Python 3.12) service that proxies the OpenF1 public API. It runs locally with uvicorn. The goal is to expose it over HTTPS via AWS without changing any business logic. The service makes outbound HTTP calls to OpenF1 and returns structured JSON — it holds no persistent state, making it well-suited for serverless.

## Goals / Non-Goals

**Goals:**
- HTTPS endpoint accessible via API Gateway URL
- Lambda executes the FastAPI app via Mangum (ASGI adapter)
- Container image packaging (avoids Lambda zip size limits with pydantic/httpx)
- CloudWatch logging for both Lambda invocations and API Gateway access logs
- TypeScript CDK for infrastructure-as-code
- Cognito User Pool for user identity and token issuance
- JWT authorizer on API Gateway protecting all `/v1/*` routes

**Non-Goals:**
- Custom domain name
- Multi-region or HA deployment
- CloudWatch alarms or dashboards
- CI/CD pipeline

## Decisions

### Lambda over ECS Fargate
Lambda has zero idle cost and API Gateway integrates natively. Lapwise is request-driven with no persistent connections or background workers. Cold starts are acceptable for a dev deployment.

### HTTP API Gateway (v2) over REST API (v1)
v2 is ~70% cheaper, has lower latency, and automatically provides HTTPS. v1 features (usage plans, per-method IAM auth, request validation) are not needed yet and can be added later by migrating the stack.

### Container image over zip deployment
`pydantic`, `httpx`, and their transitive dependencies exceed the 50 MB Lambda zip limit when combined with the Python runtime. Docker image deployment (up to 10 GB) avoids this without layer splitting.

### `mangum` with `lifespan="off"`
The FastAPI lifespan context manager creates and closes the `OpenF1Client`. Lambda containers are reused across invocations, so a persistent client would leak between requests if the lifespan never fires cleanly. With `lifespan="off"`, the client is created per-request via the dependency injection system (`deps.py`). This trades a small per-request overhead for correctness.

### `infra/` as a separate TypeScript CDK project
Keeps infrastructure concerns out of the Python service tree. The CDK project lives at `infra/` in the repo root and references `../service` as the Docker build context. This matches the common mono-repo convention and allows the infra to be deployed independently.

### Cognito JWT auth over IAM or API keys

Three options were considered:

| Option | Pros | Cons |
|---|---|---|
| IAM SigV4 | Zero extra infra, AWS-native | Requires AWS credentials for every caller — unusable for browser/mobile clients |
| API keys | Simple, any HTTP client | No user identity, manual key rotation |
| **Cognito JWT** | User identity, standard OAuth2 tokens, works with any HTTP client | More infra to provision |

Cognito JWT is chosen because callers are likely web/mobile clients that can't hold AWS credentials, and it gives user identity without writing auth logic in the FastAPI app. API Gateway v2 validates the JWT natively — the Lambda never sees an unauthenticated request.

`/healthz` is excluded from the authorizer so infrastructure health checks don't require a token.

## Risks / Trade-offs

- **Lambda cold starts**: First request after idle may take 1–3 s due to container init. → Acceptable for dev; provisioned concurrency can be added later if needed.
- **OpenF1Client per request**: Slight latency increase from TCP handshake on every call. → OpenF1 is the upstream bottleneck; the overhead is negligible.
- **Cognito token expiry**: Default access token TTL is 1 hour. Clients must handle refresh. → Standard OAuth2 behavior; document in README.
- **ECR costs**: Container images stored in ECR incur minor storage costs. → Negligible at dev scale.

## Migration Plan

1. Add `mangum` to `service/pyproject.toml` and create `lambda_handler.py`
2. Add `service/Dockerfile`
3. Create `infra/` TypeScript CDK project with Lambda, API Gateway, Cognito User Pool, and log groups
4. Run `cdk bootstrap` (one-time per account/region)
5. Run `cdk deploy` — outputs the HTTPS API Gateway URL and Cognito User Pool ID
6. Create a test user in Cognito, obtain a token, smoke-test `GET <url>/v1/sessions` with `Authorization: Bearer <token>`

**Rollback**: `cdk destroy` tears down all resources. No database or persistent state to migrate.

## Open Questions

- Which AWS region to deploy to? (defaulting to `us-east-1`)
- Should the Lambda memory/timeout be configurable via CDK context or hardcoded for now? (proposing 512 MB / 30 s as dev defaults)

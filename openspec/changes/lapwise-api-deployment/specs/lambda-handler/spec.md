## ADDED Requirements

### Requirement: Lambda entry point wraps FastAPI app
The service SHALL expose a `handler` callable in `lapwise.lambda_handler` that adapts the FastAPI ASGI app to the AWS Lambda event/context interface using Mangum 22.0.0.

#### Scenario: Handler is importable as Lambda function handler
- **WHEN** Lambda runtime imports `lapwise.lambda_handler`
- **THEN** a `handler` callable is available at module level and accepts `(event, context)` arguments

#### Scenario: HTTP request is forwarded to FastAPI
- **WHEN** API Gateway invokes the Lambda with an HTTP API (v2) payload
- **THEN** the handler translates it into an ASGI request, routes it through FastAPI, and returns a valid Lambda HTTP response with correct status code and body

#### Scenario: Lifespan events are disabled
- **WHEN** the Lambda container initializes
- **THEN** the FastAPI lifespan context manager SHALL NOT be invoked (Mangum configured with `lifespan="off"`)

#### Scenario: Existing routes remain unchanged
- **WHEN** any existing `/v1/*` or `/healthz` route is called via the Lambda handler
- **THEN** the response SHALL be identical to the local uvicorn response for the same request

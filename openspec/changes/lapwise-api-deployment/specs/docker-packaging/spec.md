## ADDED Requirements

### Requirement: Service is packaged as a Lambda container image
The service SHALL include a `Dockerfile` at `service/Dockerfile` that produces a Lambda-compatible container image using the official AWS Lambda Python 3.12 base image.

#### Scenario: Image builds successfully
- **WHEN** `docker build` is run from the `service/` directory
- **THEN** the image builds without errors and the `lapwise` package is installed

#### Scenario: Lambda handler is set as the CMD
- **WHEN** the container image is run by the Lambda runtime
- **THEN** the CMD SHALL point to `lapwise.lambda_handler.handler`

#### Scenario: Dependencies are installed from lockfile
- **WHEN** the image is built
- **THEN** all dependencies in `pyproject.toml` (including `mangum==22.0.0`) SHALL be installed using `uv` from `uv.lock`

#### Scenario: Source code is included
- **WHEN** the image is built
- **THEN** the `src/` directory containing the `lapwise` package SHALL be copied into the image

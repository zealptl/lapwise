FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR ${LAMBDA_TASK_ROOT}

COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN uv pip install --system --python /var/lang/bin/python3.12 .

CMD ["lapwise.lambda_handler.handler"]

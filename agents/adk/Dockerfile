FROM ghcr.io/astral-sh/uv:0.12.17 AS uv

FROM python:3.12-slim

LABEL org.opencontainers.image.title="A2A Travel Agent — Google ADK" \
      org.opencontainers.image.description="Google ADK travel agent with real and deterministic model modes" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
COPY --from=uv /uv /usr/local/bin/uv
COPY LICENSE NOTICE ./
COPY agents/adk/pyproject.toml agents/adk/uv.lock agents/adk/README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY agents/adk/src ./src
RUN uv sync --frozen --no-dev --no-editable

RUN useradd --no-log-init --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV AGENT_HOST=0.0.0.0
EXPOSE 4201

CMD ["adk-a2a-agent"]

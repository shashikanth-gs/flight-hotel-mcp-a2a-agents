FROM ghcr.io/astral-sh/uv:0.12.17 AS uv

FROM python:3.12-slim

LABEL org.opencontainers.image.title="Travel Fixture MCP Servers" \
      org.opencontainers.image.description="Deterministic flight and hotel fixtures for any MCP client" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
COPY --from=uv /uv /usr/local/bin/uv
COPY LICENSE NOTICE ./
COPY mcp-servers/pyproject.toml mcp-servers/uv.lock mcp-servers/README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY mcp-servers/src ./src
RUN uv sync --frozen --no-dev --no-editable

RUN useradd --no-log-init --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV MCP_HOST=0.0.0.0
EXPOSE 4301 4302

CMD ["flight-mcp"]

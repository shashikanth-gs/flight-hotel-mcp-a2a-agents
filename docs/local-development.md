# Local development

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Docker with Compose v2 for the complete topology

## Install

Each application has an independent environment and lock file:

```bash
make install
```

Run all static checks and unit tests:

```bash
make check
```

Use `make format` to apply Ruff formatting and `make lock` after intentionally changing Python
dependencies.

## Run the free integration path

```bash
cp .env.example .env
docker compose up --build flight-mcp hotel-mcp adk-stub langgraph-stub
```

Inspect service health with `docker compose ps`. Stop the topology with:

```bash
docker compose down
```

## Run services natively

Start the two MCP servers in separate terminals:

```bash
uv run --project mcp-servers flight-mcp
uv run --project mcp-servers hotel-mcp
```

Start an agent in stub mode:

```bash
cp agents/adk/.env.example agents/adk/.env
# Edit agents/adk/.env and set AGENT_MODEL_MODE=stub.
uv run --project agents/adk adk-a2a-agent
```

Or use LangGraph:

```bash
cp agents/langgraph/.env.example agents/langgraph/.env
# Edit agents/langgraph/.env and set AGENT_MODEL_MODE=stub.
uv run --project agents/langgraph langgraph-a2a-agent
```

Probe a running agent:

```bash
uv run --project agents/adk adk-a2a-probe --agent http://127.0.0.1:4201
uv run --project agents/langgraph langgraph-a2a-probe --agent http://127.0.0.1:4202
```

## Test a single package

```bash
uv run --project mcp-servers python -m unittest discover -s mcp-servers/tests -v
uv run --project agents/adk python -m unittest discover -s agents/adk/tests -v
uv run --project agents/langgraph python -m unittest discover -s agents/langgraph/tests -v
```

## Adding fixtures

Keep domain logic in `mcp-servers/src/travel_mcp/catalog.py` and data in
`mcp-servers/src/travel_mcp/data`. Add unit tests for supported aliases, date projection, totals,
validation failures, and any new tool behavior. Do not add scraped or licensed commercial data.

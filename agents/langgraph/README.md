# LangGraph travel agent

The LangGraph implementation of the [A2A Travel Playground](../../README.md). It exposes an A2A
server backed by remote flight and hotel MCP tools.

The same package supports:

- `AGENT_MODEL_MODE=stub`: deterministic LiteLLM mock completions, no provider credentials
- `AGENT_MODEL_MODE=real`: NVIDIA NIM through LiteLLM, with the configurable invocation limiter

## Interfaces

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/.well-known/agent-card.json` | A2A Agent Card |
| `POST` | `/` | A2A JSON-RPC |
| `POST` | `/rest` | A2A HTTP+JSON |

Compose publishes real mode on port 4202 and stub mode on port 4204. Both containers listen on port
4202 internally.

## Run natively

From the repository root:

```bash
uv sync --project agents/langgraph --locked
cp agents/langgraph/.env.example agents/langgraph/.env
# The example defaults to AGENT_MODEL_MODE=stub.
uv run --project agents/langgraph langgraph-a2a-agent
```

Start the flight and hotel MCP services first. See [local development](../../docs/local-development.md).

Probe a running server and run its tests:

```bash
uv run --project agents/langgraph langgraph-a2a-probe --agent http://127.0.0.1:4202
uv run --project agents/langgraph python -m unittest discover -s agents/langgraph/tests -v
```

The equivalent module entry point is
`uv run --project agents/langgraph python -m langgraph_travel_agent`.

## Implementation notes

- A ReAct graph selects between namespaced flight and hotel MCP tools.
- Stub mode creates deterministic LiteLLM mock tool calls but still exercises the MCP transport.
- Graph updates and message chunks are adapted into A2A status and artifact events.
- OpenInference LangChain instrumentation and explicit spans support optional OTLP export.
- Rate limiting applies only when real mode and `RATE_LIMIT_ENABLED=true` are both selected.

Configuration is documented in the [configuration reference](../../docs/configuration.md).

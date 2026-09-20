# Google ADK travel agent

The Google ADK implementation of the [A2A Travel Playground](../../README.md). It exposes an A2A
server backed by remote flight and hotel MCP tools.

The same package supports:

- `AGENT_MODEL_MODE=stub`: deterministic LiteLLM mock completions, no provider credentials
- `AGENT_MODEL_MODE=real`: NVIDIA NIM through LiteLLM, with the configurable invocation limiter

## Interfaces

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/.well-known/agent-card.json` | A2A Agent Card |
| `POST` | `/` | A2A JSON-RPC |

Compose publishes real mode on port 4201 and stub mode on port 4203. Both containers listen on port
4201 internally.

## Run the published image

The agent requires reachable flight and hotel MCP endpoints. With both MCP containers attached to a
Docker network as `flight-mcp` and `hotel-mcp`, start the credential-free stub agent with:

```bash
docker run --rm --network travel-a2a -p 4203:4201 \
  -e AGENT_MODEL_MODE=stub \
  -e ADK_PUBLIC_BASE_URL=http://localhost:4203 \
  -e FLIGHT_MCP_URL=http://flight-mcp:4301/mcp \
  -e HOTEL_MCP_URL=http://hotel-mcp:4302/mcp \
  shashikanthg/flight-hotel-a2a-adk:main
```

The Agent Card is available at `http://localhost:4203/.well-known/agent-card.json`. For the complete
six-service setup, use the repository's Compose file. The `main` tag tracks the default branch;
versioned releases additionally publish semantic-version and `latest` tags. Images support Linux
AMD64 and ARM64.

## Run natively

From the repository root:

```bash
uv sync --project agents/adk --locked
cp agents/adk/.env.example agents/adk/.env
# The example defaults to AGENT_MODEL_MODE=stub.
uv run --project agents/adk adk-a2a-agent
```

Start the flight and hotel MCP services first. See [local development](../../docs/local-development.md).

Probe a running server and run its tests:

```bash
uv run --project agents/adk adk-a2a-probe --agent http://127.0.0.1:4201
uv run --project agents/adk python -m unittest discover -s agents/adk/tests -v
```

The equivalent module entry point is
`uv run --project agents/adk python -m adk_travel_agent`.

## Implementation notes

- ADK's `LlmAgent` chooses between namespaced flight and hotel MCP tools.
- ADK's native A2A conversion exposes the framework agent over JSON-RPC.
- Stub mode creates deterministic LiteLLM mock tool calls but still exercises the MCP transport.
- Executor interception emits optional sideband events for lifecycle, model, tool, and completion
  activity.
- The ASGI application supports optional OpenTelemetry export.
- Rate limiting applies only when real mode and `RATE_LIMIT_ENABLED=true` are both selected.

Configuration is documented in the [configuration reference](../../docs/configuration.md).

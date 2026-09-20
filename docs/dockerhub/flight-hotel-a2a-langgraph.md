# Flight & Hotel A2A Agent — LangGraph

A LangGraph travel agent exposed through the Agent2Agent (A2A) protocol and backed by remote flight
and hotel MCP tools. One image supports both deterministic testing and a real NVIDIA NIM model.

This is a protocol playground—not a live travel or booking service.

## Runtime modes

| Mode | Configuration | Behavior |
|---|---|---|
| Stub | `AGENT_MODEL_MODE=stub` | Deterministic LiteLLM mock responses, no model credentials, no rate limit |
| Real | `AGENT_MODEL_MODE=real` | NVIDIA NIM through LiteLLM, configurable rate limit |

Stub mode still calls the real MCP servers; only the model response is mocked.

## Quick start

The agent requires reachable flight and hotel MCP endpoints. After attaching those containers to a
Docker network as `flight-mcp` and `hotel-mcp`, run the credential-free stub agent:

```bash
docker run --rm --network travel-a2a -p 4204:4202 \
  -e AGENT_MODEL_MODE=stub \
  -e LANGGRAPH_PUBLIC_BASE_URL=http://localhost:4204 \
  -e FLIGHT_MCP_URL=http://flight-mcp:4301/mcp \
  -e HOTEL_MCP_URL=http://hotel-mcp:4302/mcp \
  shashikanthg/flight-hotel-a2a-langgraph:main
```

Agent Card:

```text
http://localhost:4204/.well-known/agent-card.json
```

For the complete six-service setup, use the Compose file in the source repository.

## Real model mode

Set `AGENT_MODEL_MODE=real`, provide `NVIDIA_NIM_API_KEY`, and enable the limiter with
`RATE_LIMIT_ENABLED=true`. The reference configuration permits one agent invocation per 60 seconds.
Never place the API key directly in an image or command committed to source control.

## Interfaces

- A2A JSON-RPC at `/`
- A2A HTTP+JSON at `/rest`
- A2A Agent Card at `/.well-known/agent-card.json`
- Flight and hotel tools over remote MCP Streamable HTTP

## Tags and platforms

- `main`: current default-branch build
- `latest`: latest versioned release
- Semantic-version tags such as `1.2.3`, `1.2`, and `1`
- Platforms: `linux/amd64` and `linux/arm64`

## Project

- [Source code and complete documentation](https://github.com/shashikanth-gs/flight-hotel-mcp-a2a-agents)
- [LangGraph agent documentation](https://github.com/shashikanth-gs/flight-hotel-mcp-a2a-agents/tree/main/agents/langgraph)
- License: Apache-2.0

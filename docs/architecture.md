# Architecture

## Purpose

The playground tests whether independently implemented A2A clients and servers can discover an
agent, submit a request, stream or retrieve results, and observe MCP-backed tool use without
depending on live travel systems.

## Runtime topology

There are three source packages and six runtime services:

| Source package | Runtime services |
|---|---|
| `mcp-servers` | `flight-mcp`, `hotel-mcp` |
| `agents/adk` | `adk-real`, `adk-stub` |
| `agents/langgraph` | `langgraph-real`, `langgraph-stub` |

The real and stub services for a framework use the same image. `AGENT_MODEL_MODE` selects the
model path at runtime.

## Request path

1. An A2A client discovers an agent through its public Agent Card.
2. The client sends or streams a message through the A2A endpoint.
3. The framework agent selects an MCP tool.
4. The agent invokes the flight or hotel server over MCP Streamable HTTP.
5. The MCP server queries versioned JSON fixtures and projects the requested dates and quantities.
6. The agent returns the result as an A2A task artifact.

The MCP services own travel-domain fixtures and deterministic calculations. Agents own prompting,
tool selection, model integration, A2A adaptation, and observability. This boundary lets another
agent framework reuse the same tools without copying travel logic.

## Model modes

### Stub

Stub mode uses LiteLLM's mock-completion capability. It recognizes the documented request shapes,
creates deterministic tool calls, invokes the real MCP transport, and formats a deterministic
answer. It validates A2A and MCP integration without credentials, external model cost, or rate
limits.

The stub is intentionally narrow. It is not intended to emulate general language understanding.

### Real

Real mode sends model requests to NVIDIA NIM through LiteLLM. A process-local sliding-window
middleware limits new A2A invocations. Discovery, task reads, cancellation, and resubscription do
not consume the limit.

The default limit is one invocation per 60 seconds per process. Running multiple replicas multiplies
the effective allowance; use a shared gateway or distributed limiter if you scale the real service.

## Protocol boundaries

- A2A is the public agent interface.
- MCP is the private tool interface used by agents.
- JSON fixture files are implementation data, not public APIs.
- OpenTelemetry export is optional and disabled when its endpoint is empty.
- The sideband extension is optional and identified by
  `urn:agent-observability:sideband-events:v1`.

## Dependency isolation

Each package has a separate lock file and virtual environment. This avoids forcing the current MCP
server SDK and framework-specific MCP client adapters into one Python dependency graph. The
containers preserve the same isolation.

## Repository boundary

The MCP servers and agents intentionally live in one repository because they form one
interoperability playground and share a release, fixture contract, Compose topology, and end-to-end
compatibility tests. The MCP servers do not depend on A2A and work directly with Claude Code,
compatible IDEs, and custom MCP clients. All components remain separate Python packages and
container images, so consumers can deploy or reuse only what they need.

Splitting the MCP servers into their own repository would add cross-repository version pinning,
release coordination, and integration-test setup. That becomes worthwhile only if the MCP servers
develop an independent product lifecycle, accept unrelated consumers, require separate ownership,
or need compatibility guarantees beyond this playground. Until then, the monorepo is the simpler
and more reliable public interface.

## Deliberate non-goals

- Live airline or hotel inventory
- Booking, payment, or personally identifiable information
- User authentication or multi-tenancy
- A distributed production rate limiter
- Long-term task persistence

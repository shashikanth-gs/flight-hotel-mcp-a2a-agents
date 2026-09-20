# Configuration reference

Configuration is supplied through environment variables. Root Compose defaults are suitable for
localhost. Component `.env.example` files support native development.

## Agent configuration

| Variable | Default | Description |
|---|---|---|
| `AGENT_MODEL_MODE` | `real` | `real` for NVIDIA NIM or `stub` for deterministic LiteLLM mocks |
| `NVIDIA_NIM_API_KEY` | Empty | Required only in real mode |
| `NVIDIA_MODEL` | Set by examples | LiteLLM model identifier; real mode requires the `nvidia_nim/` prefix |
| `NVIDIA_NIM_API_BASE` | NVIDIA hosted API | Replace for a compatible private NIM deployment |
| `AGENT_HOST` | `127.0.0.1` | Bind address |
| `ADK_AGENT_PORT` | `4201` | Internal ADK listen port |
| `LANGGRAPH_AGENT_PORT` | `4202` | Internal LangGraph listen port |
| `ADK_PUBLIC_BASE_URL` | Derived from host/port | Public URL written into the ADK Agent Card |
| `LANGGRAPH_PUBLIC_BASE_URL` | Derived from host/port | Public URL written into the LangGraph Agent Card |
| `FLIGHT_MCP_URL` | `http://127.0.0.1:4301/mcp` | Flight MCP Streamable HTTP endpoint |
| `HOTEL_MCP_URL` | `http://127.0.0.1:4302/mcp` | Hotel MCP Streamable HTTP endpoint |
| `RATE_LIMIT_ENABLED` | `false` | Enables the invocation limiter; effective only in real mode |
| `RATE_LIMIT_REQUESTS` | `1` | Allowed invocations in one window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Sliding-window duration |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | Local Phoenix endpoint natively; empty in Compose | OTLP/HTTP trace endpoint; empty disables export |
| `OTEL_EXPORTER_OTLP_HEADERS` | Empty | Standard OpenTelemetry exporter headers |
| `SIDEBAND_EXTENSION_URI` | Project sideband URI | Advertised A2A extension identifier |

Set the public base URL to the externally reachable HTTPS origin in hosted environments. Never
publish `0.0.0.0` or an internal Compose hostname in an Agent Card.

## MCP server configuration

| Variable | Default | Description |
|---|---|---|
| `MCP_HOST` | `127.0.0.1` | Bind address |
| `FLIGHT_MCP_PORT` | `4301` | Flight server listen port |
| `HOTEL_MCP_PORT` | `4302` | Hotel server listen port |
| `MCP_ALLOWED_HOSTS` | Localhost for the relevant port | Comma-separated Host values accepted by DNS-rebinding protection |

For public deployment, include the external host in `MCP_ALLOWED_HOSTS`. Include a port only when
clients send a non-default port in the HTTP `Host` header.

## Secrets

Only the real agents require a secret. Keep `NVIDIA_NIM_API_KEY` in the hosting platform's secret
store or an uncommitted local `.env`. The repository ignores all `.env.*` files except checked-in
examples.

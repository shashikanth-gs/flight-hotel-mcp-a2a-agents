# Deployment

The repository ships a local Compose topology. For hosting, deploy each Compose service as an
independent container or translate its environment into the platform's service definition.

## Recommended public topology

Expose the four A2A agents as public HTTPS services. Keep the MCP services on a private service
network unless direct MCP interoperability testing is part of the goal.

| Service | Public by default | Replicas |
|---|---|---|
| Flight MCP | No | 1 or more |
| Hotel MCP | No | 1 or more |
| ADK stub | Yes | 1 or more |
| LangGraph stub | Yes | 1 or more |
| ADK real | Yes | Exactly 1 with the built-in limiter |
| LangGraph real | Yes | Exactly 1 with the built-in limiter |

## Required platform settings

- Build all images from the repository root using their component Dockerfiles.
- Terminate TLS at the platform ingress.
- Set each agent's public base URL to its external HTTPS origin.
- Inject `NVIDIA_NIM_API_KEY` from a secret store only into real agents.
- Restrict MCP ingress to the agent services where possible.
- Configure `MCP_ALLOWED_HOSTS` for the hostnames received by each MCP service.
- Keep health checks enabled.
- Set CPU, memory, and request-time limits appropriate for the selected model.
- Forward application logs and optionally configure an OTLP trace endpoint.

Example build commands:

```bash
docker build -f mcp-servers/Dockerfile -t flight-hotel-mcp-server:0.2.0 .
docker build -f agents/adk/Dockerfile -t flight-hotel-a2a-adk:0.2.0 .
docker build -f agents/langgraph/Dockerfile -t flight-hotel-a2a-langgraph:0.2.0 .
```

Start the same agent image with `AGENT_MODEL_MODE=real` and `AGENT_MODEL_MODE=stub` to create
the two variants.

## Security boundary

These services do not implement authentication, authorization, abuse prevention, or tenant
isolation. The one-per-minute middleware is a cost guard, not a security control.

For an internet-facing deployment, place the agents behind a gateway that supplies:

- TLS and trusted proxy handling
- Authentication when the playground should not be anonymous
- Per-client rate limits and request-size limits
- Timeouts and concurrency limits
- Access logs without secrets or sensitive prompts
- Network policy preventing unnecessary access to MCP services

The built-in limiter is process-local. Do not horizontally scale a real agent while relying on it
for a global one-request-per-minute ceiling. Use a shared gateway or distributed store first.

## Data and privacy

The fixture tools require no user data. Do not send personal, payment, or confidential information
to this playground. Review the model provider's data-handling terms before enabling real mode.

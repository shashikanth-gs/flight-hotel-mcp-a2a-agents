# Flight & Hotel MCP + A2A Helm chart

This chart deploys the travel interoperability playground using the published multi-architecture
Docker images.

The default installation requires no credentials and creates four workloads:

- Flight MCP fixture server
- Hotel MCP fixture server
- Google ADK A2A agent in deterministic stub mode
- LangGraph A2A agent in deterministic stub mode

The ADK and LangGraph real NVIDIA NIM agents are available but disabled by default.

## Install

```bash
helm upgrade --install travel ./charts/flight-hotel-mcp-a2a \
  --namespace travel \
  --create-namespace
```

Inspect the generated resources without installing them:

```bash
helm lint ./charts/flight-hotel-mcp-a2a
helm template travel ./charts/flight-hotel-mcp-a2a --namespace travel
```

## Access the stub agents

Services are `ClusterIP` by default because the playground has no authentication. For local access:

```bash
kubectl --namespace travel port-forward \
  service/travel-flight-hotel-mcp-a2a-adk-stub 4203:4201
```

```bash
kubectl --namespace travel port-forward \
  service/travel-flight-hotel-mcp-a2a-langgraph-stub 4204:4202
```

The Agent Cards are then available at:

- `http://localhost:4203/.well-known/agent-card.json`
- `http://localhost:4204/.well-known/agent-card.json`

If an A2A client follows the URL advertised inside an Agent Card, set the corresponding
`publicBaseUrl` to the port-forwarded URL during installation. The default advertised URLs are the
in-cluster Service addresses.

## Enable real NVIDIA agents

Create the API key outside the values file:

```bash
kubectl --namespace travel create secret generic nvidia-nim \
  --from-literal=NVIDIA_NIM_API_KEY="$NVIDIA_NIM_API_KEY"
```

Enable either or both real agents using that Secret:

```bash
helm upgrade --install travel ./charts/flight-hotel-mcp-a2a \
  --namespace travel \
  --create-namespace \
  --set nvidia.existingSecret=nvidia-nim \
  --set agents.adk.real.enabled=true \
  --set agents.langgraph.real.enabled=true
```

Real agents default to one invocation per 60 seconds and exactly one replica. The built-in limiter
is process-local, so the schema prevents multiple real-agent replicas. Use a shared gateway limiter
before changing that architecture.

For hosted agents, set each `publicBaseUrl` to the external HTTPS origin written into its Agent Card:

```yaml
agents:
  adk:
    real:
      publicBaseUrl: https://adk-real.example.com
  langgraph:
    real:
      publicBaseUrl: https://langgraph-real.example.com
```

## Important values

| Value | Default | Purpose |
|---|---|---|
| `global.imageTag` | `main` | Shared default image tag |
| `mcp.flight.enabled` | `true` | Deploy the flight MCP service |
| `mcp.hotel.enabled` | `true` | Deploy the hotel MCP service |
| `agents.adk.stub.enabled` | `true` | Deploy the ADK stub agent |
| `agents.langgraph.stub.enabled` | `true` | Deploy the LangGraph stub agent |
| `agents.adk.real.enabled` | `false` | Deploy the ADK NVIDIA agent |
| `agents.langgraph.real.enabled` | `false` | Deploy the LangGraph NVIDIA agent |
| `nvidia.existingSecret` | Empty | Existing Secret containing the NIM key |
| `nvidia.secretKey` | `NVIDIA_NIM_API_KEY` | Key within the existing Secret |
| `agents.mcp.flightUrl` | Internal chart Service | Override for an external flight MCP server |
| `agents.mcp.hotelUrl` | Internal chart Service | Override for an external hotel MCP server |
| `observability.otlpEndpoint` | Empty | Optional OTLP/HTTP traces endpoint |

See [`values.yaml`](values.yaml) for images, resources, Services, scheduling, security contexts, and
all mode-specific settings.

## Security

- Containers run as UID/GID 10001 with a read-only root filesystem and dropped capabilities.
- Kubernetes service-account token mounting is disabled.
- The chart creates no Ingress and no RBAC permissions.
- Prefer `nvidia.existingSecret`; `nvidia.apiKey` exists only for disposable local testing.
- Put public agents behind a gateway providing TLS, authentication, request limits, and timeouts.
- Keep MCP Services private unless direct external MCP testing is intentional.

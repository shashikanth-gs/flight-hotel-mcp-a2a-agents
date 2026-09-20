# Travel fixture MCP servers

Two independent Streamable HTTP MCP services built with Python and the official MCP Python SDK 2.x.
Both services are packaged together because they share a small deterministic fixture catalog, but
they run as separate processes.

| Command | Default endpoint | Tools |
|---|---|---|
| `flight-mcp` | `http://127.0.0.1:4301/mcp` | `search_flights`, `list_routes`, `list_airports` |
| `hotel-mcp` | `http://127.0.0.1:4302/mcp` | `search_hotels`, `get_hotel`, `list_hotel_cities` |

Health endpoints are available at `/health` on each service.

These servers have no dependency on A2A or on the included agents. Any client that supports MCP
Streamable HTTP can connect directly, including Claude Code, compatible IDEs, and custom MCP
clients.

## Run the published image

The image contains both server commands. Run one container for each independent MCP endpoint:

```bash
docker run --rm -p 4301:4301 \
  -e MCP_ALLOWED_HOSTS=localhost:4301,127.0.0.1:4301 \
  shashikanthg/flight-hotel-mcp-server:main flight-mcp
```

```bash
docker run --rm -p 4302:4302 \
  -e MCP_ALLOWED_HOSTS=localhost:4302,127.0.0.1:4302 \
  shashikanthg/flight-hotel-mcp-server:main hotel-mcp
```

The MCP endpoints are `http://localhost:4301/mcp` and `http://localhost:4302/mcp`. The `main` tag
tracks the default branch; versioned releases additionally publish semantic-version and `latest`
tags. Images support Linux AMD64 and ARM64.

## Run natively

From the repository root:

```bash
uv sync --project mcp-servers --locked
uv run --project mcp-servers flight-mcp
```

In another terminal:

```bash
uv run --project mcp-servers hotel-mcp
```

Connect the running services to Claude Code:

```bash
claude mcp add --transport http travel-flights http://localhost:4301/mcp
claude mcp add --transport http travel-hotels http://localhost:4302/mcp
```

[Claude Code supports remote HTTP MCP servers](https://code.claude.com/docs/en/mcp) and treats
`streamable-http` as an alias for the `http` transport. Other clients should use their equivalent
Streamable HTTP configuration.

Run the unit tests:

```bash
uv run --project mcp-servers python -m unittest discover -s mcp-servers/tests -v
```

## Data contract

The services read a manually curated JSON test catalog: 16 airports, 15 flight templates over 14
directional routes, and 12 hotel fixtures in 10 cities. Coverage is primarily India-centric, with
selected outbound international routes. All prices are simulated INR values.

Airport identities are real-world facts, but flight schedules, flight numbers, availability,
hotels, and prices are fictional and cannot be booked. Searches project fixture values onto the
requested dates and calculate totals at runtime; they do not query live travel systems.

See the [complete fixture dataset contract](../docs/data-and-limitations.md) for exact coverage,
future-date behavior, and unsupported-query semantics, and see the
[configuration reference](../docs/configuration.md).

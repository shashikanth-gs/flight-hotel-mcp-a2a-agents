# Flight & Hotel MCP Fixture Servers

Deterministic flight and hotel test data exposed through two independent Model Context Protocol
(MCP) Streamable HTTP servers. Use the image with any compatible MCP client or as the tool layer
for the companion A2A agents.

This is a testing and interoperability image—not a live travel or booking service.

## Included servers

| Command | Endpoint | Tools |
|---|---|---|
| `flight-mcp` | `http://localhost:4301/mcp` | `search_flights`, `list_routes`, `list_airports` |
| `hotel-mcp` | `http://localhost:4302/mcp` | `search_hotels`, `get_hotel`, `list_hotel_cities` |

Each server also exposes `/health`.

## Quick start

Run one container for each service:

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

Claude Code example:

```bash
claude mcp add --transport http travel-flights http://localhost:4301/mcp
claude mcp add --transport http travel-hotels http://localhost:4302/mcp
```

## Fixture data

- 16 airports: 8 in India and 8 international
- 15 flight templates across 14 directional routes
- 12 hotel fixtures across 10 cities
- Simulated INR prices
- Requested future dates are applied dynamically to fixture schedules

Airport identities are real-world facts. Flight numbers, schedules, hotels, availability, and
prices are fictional and cannot be booked.

## Tags and platforms

- `main`: current default-branch build
- `latest`: latest versioned release
- Semantic-version tags such as `1.2.3`, `1.2`, and `1`
- Platforms: `linux/amd64` and `linux/arm64`

## Project

- [Source code and complete documentation](https://github.com/shashikanth-gs/flight-hotel-mcp-a2a-agents)
- [Dataset coverage and limitations](https://github.com/shashikanth-gs/flight-hotel-mcp-a2a-agents/blob/main/docs/data-and-limitations.md)
- License: Apache-2.0

from __future__ import annotations

import os

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from travel_mcp import __version__
from travel_mcp.catalog import list_airports, list_routes, search_flights


def _transport_security() -> TransportSecuritySettings:
    allowed_hosts = [
        value.strip()
        for value in os.getenv("MCP_ALLOWED_HOSTS", "127.0.0.1:4301,localhost:4301").split(",")
        if value.strip()
    ]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
    )


def build_server() -> MCPServer:
    server = MCPServer(
        "Travel Fixture Flights",
        instructions=(
            "Search deterministic flight fixtures. All schedules, seats, and prices are simulated."
        ),
        version=__version__,
    )
    server.tool()(search_flights)
    server.tool()(list_routes)
    server.tool()(list_airports)

    @server.custom_route("/health", methods=["GET"])
    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "flight-mcp"})

    return server


mcp = build_server()
app = mcp.streamable_http_app(
    stateless_http=True,
    json_response=True,
    transport_security=_transport_security(),
)


def main() -> None:
    mcp.run(
        transport="streamable-http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("FLIGHT_MCP_PORT", "4301")),
        stateless_http=True,
        json_response=True,
        transport_security=_transport_security(),
    )


if __name__ == "__main__":
    main()

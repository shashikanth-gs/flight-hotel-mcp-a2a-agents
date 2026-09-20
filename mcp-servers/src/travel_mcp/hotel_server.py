from __future__ import annotations

import os

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from travel_mcp import __version__
from travel_mcp.catalog import get_hotel, list_hotel_cities, search_hotels


def _transport_security() -> TransportSecuritySettings:
    allowed_hosts = [
        value.strip()
        for value in os.getenv("MCP_ALLOWED_HOSTS", "127.0.0.1:4302,localhost:4302").split(",")
        if value.strip()
    ]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
    )


def build_server() -> MCPServer:
    server = MCPServer(
        "Travel Fixture Hotels",
        instructions="Search deterministic hotel fixtures. Listings and prices are simulated.",
        version=__version__,
    )
    server.tool()(search_hotels)
    server.tool()(get_hotel)
    server.tool()(list_hotel_cities)

    @server.custom_route("/health", methods=["GET"])
    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "hotel-mcp"})

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
        port=int(os.getenv("HOTEL_MCP_PORT", "4302")),
        stateless_http=True,
        json_response=True,
        transport_security=_transport_security(),
    )


if __name__ == "__main__":
    main()

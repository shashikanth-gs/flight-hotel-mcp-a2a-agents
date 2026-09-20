from __future__ import annotations

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from adk_travel_agent.config import Settings

FLIGHT_TOOLS = ["search_flights", "list_routes", "list_airports"]
HOTEL_TOOLS = ["search_hotels", "get_hotel", "list_hotel_cities"]


def adk_mcp_toolsets(settings: Settings) -> list[McpToolset]:
    return [
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.flight_mcp_url,
                timeout=10,
                sse_read_timeout=60,
            ),
            tool_filter=FLIGHT_TOOLS,
            tool_name_prefix="flights",
        ),
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.hotel_mcp_url,
                timeout=10,
                sse_read_timeout=60,
            ),
            tool_filter=HOTEL_TOOLS,
            tool_name_prefix="hotels",
        ),
    ]


def mcp_server_urls(settings: Settings) -> dict[str, str]:
    return {"flights": settings.flight_mcp_url, "hotels": settings.hotel_mcp_url}

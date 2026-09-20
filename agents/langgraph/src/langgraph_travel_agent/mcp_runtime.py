from __future__ import annotations

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from langgraph_travel_agent.config import Settings

ALLOWED_TOOLS = {
    "flights_search_flights",
    "flights_list_routes",
    "flights_list_airports",
    "hotels_search_hotels",
    "hotels_get_hotel",
    "hotels_list_hotel_cities",
}


def langchain_mcp_client(settings: Settings) -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "flights": {"url": settings.flight_mcp_url, "transport": "http"},
            "hotels": {"url": settings.hotel_mcp_url, "transport": "http"},
        },
        tool_name_prefix=True,
    )


async def langchain_mcp_tools(client: MultiServerMCPClient) -> list[BaseTool]:
    tools = await client.get_tools()
    return [tool for tool in tools if tool.name in ALLOWED_TOOLS]


def mcp_server_urls(settings: Settings) -> dict[str, str]:
    return {"flights": settings.flight_mcp_url, "hotels": settings.hotel_mcp_url}

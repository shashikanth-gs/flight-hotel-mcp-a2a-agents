from __future__ import annotations

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentExtension,
    AgentInterface,
    AgentSkill,
)

from langgraph_travel_agent import __version__


def agent_card(
    *,
    name: str,
    description: str,
    base_url: str,
    sideband_uri: str,
    skills: list[AgentSkill],
    rest_url: str | None = None,
) -> AgentCard:
    interfaces = [
        AgentInterface(
            url=f"{base_url}/",
            protocol_binding="JSONRPC",
            protocol_version="1.0",
            tenant="",
        )
    ]
    if rest_url:
        interfaces.append(
            AgentInterface(
                url=rest_url,
                protocol_binding="HTTP+JSON",
                protocol_version="1.0",
                tenant="",
            )
        )
    return AgentCard(
        name=name,
        description=description,
        supported_interfaces=interfaces,
        version=__version__,
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            extended_agent_card=False,
            extensions=[
                AgentExtension(
                    uri=sideband_uri,
                    description="Provisional generic execution events for interoperability tests.",
                    required=False,
                    params={"schemaVersion": 1},
                )
            ],
        ),
        default_input_modes=["text/plain", "text/markdown", "application/json"],
        default_output_modes=["text/plain", "text/markdown", "application/json"],
        skills=skills,
    )

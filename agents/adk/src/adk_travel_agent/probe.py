from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass

import httpx
from a2a.client import ClientCallContext, ClientConfig, create_client
from a2a.client.card_resolver import A2ACardResolver
from a2a.client.service_parameters import ServiceParametersFactory, with_a2a_extensions
from a2a.helpers import new_text_message
from a2a.types import Role, SendMessageRequest
from google.protobuf.json_format import MessageToDict

from adk_travel_agent.config import DEFAULT_SIDEBAND_URI


@dataclass
class ProbeResult:
    agent: str
    url: str
    event_counts: dict[str, int]
    states: list[str]
    artifacts: list[str]
    artifact_texts: list[str]
    advertised_extensions: list[str]
    negotiated_extensions: list[str]
    sideband_events: int
    agent_messages: list[str]
    passed: bool


def _advertised_extensions(card: object) -> list[str]:
    capabilities = getattr(card, "capabilities", None)
    return sorted(
        extension.uri
        for extension in getattr(capabilities, "extensions", [])
        if getattr(extension, "uri", "")
    )


async def probe_agent(
    base_url: str,
    prompt: str,
    *,
    extension_uri: str = DEFAULT_SIDEBAND_URI,
    timeout_seconds: float = 90,
) -> ProbeResult:
    async with httpx.AsyncClient(timeout=timeout_seconds) as http_client:
        card = await A2ACardResolver(http_client, base_url).get_agent_card()
        advertised = _advertised_extensions(card)
        negotiated = [extension_uri] if extension_uri in advertised else []
        context = None
        if negotiated:
            context = ClientCallContext(
                service_parameters=ServiceParametersFactory.create(
                    [with_a2a_extensions(negotiated)]
                )
            )

        client = await create_client(
            agent=card,
            client_config=ClientConfig(streaming=True, httpx_client=http_client),
        )
        event_counts: dict[str, int] = {}
        states: list[str] = []
        artifacts: list[str] = []
        artifact_texts: list[str] = []
        sideband_events = 0
        agent_messages: list[str] = []
        try:
            request = SendMessageRequest(message=new_text_message(prompt, role=Role.ROLE_USER))
            async for response in client.send_message(request, context=context):
                payload = MessageToDict(response, preserving_proto_field_name=True)
                kind = next(iter(payload), "unknown")
                event_counts[kind] = event_counts.get(kind, 0) + 1
                event = payload.get(kind, {})
                if not isinstance(event, dict):
                    continue
                if kind in {"task", "status_update"}:
                    state = str(event.get("status", {}).get("state", ""))
                    if state:
                        states.append(state)
                if kind == "artifact_update":
                    artifact = event.get("artifact", {})
                    artifacts.append(str(artifact.get("name", "")))
                    text = "\n".join(
                        str(part.get("text", ""))
                        for part in artifact.get("parts", [])
                        if isinstance(part, dict) and part.get("text")
                    ).strip()
                    if text:
                        artifact_texts.append(text)
                if kind == "task" and isinstance(event.get("artifacts"), list):
                    artifacts.extend(
                        str(artifact.get("name", ""))
                        for artifact in event["artifacts"]
                        if isinstance(artifact, dict)
                    )
                metadata = event.get("metadata", {})
                if isinstance(metadata, dict):
                    extension_events = metadata.get(f"{extension_uri}/events", [])
                    if isinstance(extension_events, list):
                        sideband_events += len(extension_events)
                message = event if kind == "message" else event.get("status", {}).get("message")
                if isinstance(message, dict) and str(message.get("role", "")).upper().endswith(
                    "AGENT"
                ):
                    text = "\n".join(
                        str(part.get("text", ""))
                        for part in message.get("parts", [])
                        if isinstance(part, dict) and part.get("text")
                    ).strip()
                    if text:
                        agent_messages.append(text)
        finally:
            await client.close()

        terminal_state = states[-1] if states else ""
        return ProbeResult(
            agent=card.name,
            url=base_url,
            event_counts=event_counts,
            states=states,
            artifacts=artifacts,
            artifact_texts=artifact_texts,
            advertised_extensions=advertised,
            negotiated_extensions=negotiated,
            sideband_events=sideband_events,
            agent_messages=agent_messages,
            passed=terminal_state == "TASK_STATE_COMPLETED",
        )


async def _run(args: argparse.Namespace) -> int:
    results = [
        await probe_agent(
            url,
            args.prompt,
            extension_uri=args.extension_uri,
            timeout_seconds=args.timeout,
        )
        for url in args.agent
    ]
    print(json.dumps([asdict(result) for result in results], indent=2))
    return 0 if all(result.passed for result in results) else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe A2A agents with the official Python SDK; no workbench code is used."
    )
    parser.add_argument(
        "--agent",
        action="append",
        default=[],
        help="Agent base URL. Repeat to probe multiple agents.",
    )
    parser.add_argument(
        "--prompt",
        default="Plan three days in Barcelona for two travelers and include a local budget.",
    )
    parser.add_argument("--extension-uri", default=DEFAULT_SIDEBAND_URI)
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()
    if not args.agent:
        args.agent = ["http://127.0.0.1:4201"]
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()

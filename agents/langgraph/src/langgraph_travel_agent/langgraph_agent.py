from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from typing import Any

import uvicorn
from a2a.helpers import new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentSkill, Message, Part, Role, TaskState
from fastapi import FastAPI
from google.protobuf.json_format import ParseDict
from google.protobuf.struct_pb2 import Value
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from openinference.instrumentation.langchain import LangChainInstrumentor

from langgraph_travel_agent import __version__
from langgraph_travel_agent.cards import agent_card
from langgraph_travel_agent.config import Settings, load_settings
from langgraph_travel_agent.intent import RequestIntent, classify_request
from langgraph_travel_agent.mcp_runtime import langchain_mcp_client, langchain_mcp_tools
from langgraph_travel_agent.rate_limit import InvocationRateLimitMiddleware
from langgraph_travel_agent.sideband import extension_metadata, sideband_event
from langgraph_travel_agent.stub_model import StubChatLiteLLM
from langgraph_travel_agent.telemetry import configure_telemetry, instrument_asgi, traced_span

LOGGER = logging.getLogger(__name__)

AGENT_INSTRUCTION = """/no_think
You are a concise A2A travel fixture agent. Use flights_search_flights for flight requests that
include origin, destination, and a YYYY-MM-DD departure date. Use hotels_search_hotels for hotel
requests that include a city, check-in date, and check-out date. Use the catalog tools when the
user asks what routes, airports, or cities are supported. Ask for missing required fields. Invoke
at most one MCP tool per request. Always include the relevant MCP result and state that schedules,
availability, listings, and prices are simulated fixture data that cannot be booked. Never invent
a result when an MCP tool returns no match. Keep answers concise and use Markdown when useful.
""".strip()


def _content_text(message: AnyMessage) -> str:
    if isinstance(message.content, str):
        return message.content
    return json.dumps(message.content, ensure_ascii=False)


def _json_part(value: dict[str, Any]) -> Part:
    proto_value = Value()
    ParseDict(value, proto_value)
    return Part(data=proto_value, media_type="application/json")


def _agent_message(text: str, context_id: str, task_id: str) -> Message:
    return Message(
        message_id=str(uuid.uuid4()),
        context_id=context_id,
        task_id=task_id,
        role=Role.ROLE_AGENT,
        parts=[Part(text=text, media_type="text/plain")],
    )


def _last_agent_text(messages: list[AnyMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not getattr(message, "tool_calls", None):
            text = _content_text(message).strip()
            if text:
                return text
    raise RuntimeError("The LangGraph agent completed without an answer.")


def _streamed_text(message: AnyMessage) -> str:
    """Return only user-visible text deltas, never tool-call argument chunks."""
    if not isinstance(message, AIMessageChunk):
        return ""
    if isinstance(message.content, str):
        return message.content
    if not isinstance(message.content, list):
        return ""
    text: list[str] = []
    for block in message.content:
        if isinstance(block, str):
            text.append(block)
        elif isinstance(block, dict) and block.get("type") in {"text", "text-delta"}:
            value = block.get("text")
            if isinstance(value, str):
                text.append(value)
    return "".join(text)


def _tool_names(update: Any) -> list[str]:
    if not isinstance(update, dict):
        return []
    messages = update.get("messages", [])
    if not isinstance(messages, list):
        return []
    return sorted(
        {
            str(getattr(message, "name", ""))
            for message in messages
            if getattr(message, "type", "") == "tool" and getattr(message, "name", "")
        }
    )


def _parse_json_object(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def _model(settings: Settings) -> ChatLiteLLM:
    if settings.model_mode == "stub":
        return StubChatLiteLLM(
            model="openai/a2a-fixture-stub",
            api_key="fixture-key",
            temperature=0,
            max_tokens=2048,
            streaming=False,
            disable_streaming=True,
            model_kwargs={"parallel_tool_calls": False},
            max_retries=0,
        )
    return ChatLiteLLM(
        model=settings.model,
        api_key=settings.nvidia_api_key,
        api_base=settings.nvidia_api_base,
        temperature=0,
        max_tokens=2048,
        streaming=True,
        model_kwargs={"parallel_tool_calls": False},
        max_retries=2,
    )


async def _generate_structured_artifact(
    model: ChatLiteLLM,
    request_text: str,
    narrative: str,
) -> dict[str, Any]:
    prompt = {
        "userRequest": request_text,
        "generatedNarrative": narrative,
        "requiredShape": {
            "title": "string",
            "destination": "string or null",
            "duration": "string or null",
            "travelers": "number or null",
            "summary": "string",
            "days": [{"day": "number", "title": "string", "activities": ["string"]}],
            "budget": {
                "currency": "string",
                "estimatedTotal": "number or null",
                "items": [{"category": "string", "amount": "number"}],
            },
            "assumptions": ["string"],
        },
    }
    with traced_span(
        "LLM",
        "llm.trip_plan.structure",
        {
            "gen_ai.operation.name": "chat",
            "gen_ai.request.model": model.model,
            "gen_ai.provider.name": "nvidia_nim",
        },
    ):
        response = await model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "/no_think\nConvert the supplied model-generated travel answer into one "
                        "JSON object. "
                        "Return JSON only, with no Markdown fence. Preserve the answer rather than "
                        "inventing a second plan. Use null when a value is unavailable."
                    )
                ),
                HumanMessage(content=json.dumps(prompt, ensure_ascii=False)),
            ],
            response_format={"type": "json_object"},
        )
    parsed = _parse_json_object(_content_text(response))
    artifact = parsed or {
        "title": "Simulated travel plan",
        "summary": narrative,
        "days": [],
        "budget": {"currency": "unspecified", "estimatedTotal": None, "items": []},
        "assumptions": [],
    }
    return {
        "schemaVersion": 1,
        "simulated": True,
        "source": {
            "type": "model-generated-test-content",
            "provider": "nvidia_nim",
            "liveAvailability": False,
            "bookingPerformed": False,
        },
        **artifact,
    }


class LangGraphAgentExecutor(AgentExecutor):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = _model(settings)
        self.mcp_client = langchain_mcp_client(settings)
        self.graph: Any | None = None
        self._graph_lock = asyncio.Lock()

    async def _graph(self) -> Any:
        if self.graph is not None:
            return self.graph
        async with self._graph_lock:
            if self.graph is None:
                tools = await langchain_mcp_tools(self.mcp_client)
                tool_capable_model = self.model.bind_tools(
                    tools,
                    parallel_tool_calls=False,
                )
                self.graph = create_react_agent(
                    tool_capable_model,
                    tools,
                    prompt=AGENT_INSTRUCTION,
                    checkpointer=MemorySaver(),
                    name="langgraph_travel_assistant",
                )
        return self.graph

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if task is None:
            if context.message is None:
                raise ValueError("An A2A message is required to create a task.")
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        task_id = task.id
        context_id = task.context_id
        query = context.get_user_input()
        intent: RequestIntent = classify_request(query)
        updater = TaskUpdater(event_queue, task_id, context_id)
        sideband_enabled = self.settings.sideband_uri in context.requested_extensions
        await updater.start_work()

        with traced_span(
            "AGENT",
            "langgraph.agent.execute",
            {
                "gen_ai.agent.name": "langgraph_travel_assistant",
                "a2a.task.id": task_id,
                "a2a.context.id": context_id,
                "agent.request.intent": intent,
            },
        ):
            await updater.update_status(
                TaskState.TASK_STATE_WORKING,
                metadata=extension_metadata(
                    self.settings.sideband_uri,
                    sideband_enabled,
                    sideband_event(
                        "execution.started",
                        "LangGraph execution started",
                        data={"framework": "langgraph", "intent": intent},
                        taskId=task_id,
                        contextId=context_id,
                    ),
                ),
            )
            graph = await self._graph()
            config = {"configurable": {"thread_id": context_id}}
            response_artifact_id = str(uuid.uuid4())
            response_artifact_started = False
            pending_text = ""
            response_metadata = {
                "framework": "langgraph",
                "contentRole": "model-response",
                "streamingSource": (
                    "litellm.mock" if self.settings.model_mode == "stub" else "langgraph.messages"
                ),
            }
            stream_modes = (
                ["updates"] if self.settings.model_mode == "stub" else ["updates", "messages"]
            )
            async for stream_part in graph.astream(
                {"messages": [HumanMessage(content=query)]},
                config=config,
                stream_mode=stream_modes,
                version="v2",
            ):
                if not isinstance(stream_part, dict):
                    continue
                stream_type = stream_part.get("type")
                stream_data = stream_part.get("data")
                if stream_type == "messages" and isinstance(stream_data, (list, tuple)):
                    message_chunk = stream_data[0] if stream_data else None
                    text = _streamed_text(message_chunk)
                    if not text:
                        continue
                    # Hold one provider chunk so the actual final delta can carry
                    # last_chunk=true without inventing an empty protocol part.
                    if pending_text:
                        await updater.add_artifact(
                            [Part(text=pending_text, media_type="text/markdown")],
                            artifact_id=response_artifact_id,
                            name="response.md",
                            metadata=response_metadata,
                            append=response_artifact_started,
                            last_chunk=False,
                        )
                        response_artifact_started = True
                    pending_text = text
                    continue
                if stream_type != "updates" or not isinstance(stream_data, dict):
                    continue
                update = stream_data
                node_name = next(iter(update), "unknown")
                node_update = update.get(node_name, {})
                tools = _tool_names(node_update)
                event = (
                    sideband_event(
                        "mcp.tool.completed",
                        "MCP tool invocation completed",
                        data={"framework": "langgraph", "node": node_name, "tools": tools},
                        taskId=task_id,
                        contextId=context_id,
                    )
                    if tools
                    else sideband_event(
                        "graph.node.completed",
                        "Graph node completed",
                        data={"framework": "langgraph", "node": node_name},
                        taskId=task_id,
                        contextId=context_id,
                    )
                )
                await updater.update_status(
                    TaskState.TASK_STATE_WORKING,
                    metadata=extension_metadata(
                        self.settings.sideband_uri,
                        sideband_enabled,
                        event,
                    ),
                )
                await asyncio.sleep(0.15)

            snapshot = await graph.aget_state(config)
            messages = list(snapshot.values.get("messages", []))
            answer = _last_agent_text(messages)
            if pending_text:
                await updater.add_artifact(
                    [Part(text=pending_text, media_type="text/markdown")],
                    artifact_id=response_artifact_id,
                    name="response.md",
                    metadata=response_metadata,
                    append=response_artifact_started,
                    last_chunk=True,
                )
            else:
                # Some providers expose a streaming transport but return one
                # aggregated model message. It is still a valid single-chunk
                # A2A artifact and must not be presented as token streaming.
                await updater.add_artifact(
                    [Part(text=answer, media_type="text/markdown")],
                    artifact_id=response_artifact_id,
                    name="response.md",
                    metadata=response_metadata,
                    append=False,
                    last_chunk=True,
                )
            artifact_names: list[str] = ["response.md"]

            if intent == "travel_plan":
                structured_result = await _generate_structured_artifact(self.model, query, answer)
                await updater.add_artifact(
                    [_json_part(structured_result)],
                    name="trip-plan.json",
                    metadata={
                        "framework": "langgraph",
                        "contentRole": "structured-model-output",
                    },
                    last_chunk=True,
                )
                artifact_names.append("trip-plan.json")

            await updater.update_status(
                TaskState.TASK_STATE_WORKING,
                metadata=extension_metadata(
                    self.settings.sideband_uri,
                    sideband_enabled,
                    sideband_event(
                        "execution.finalizing",
                        "LangGraph execution finalizing",
                        data={"intent": intent, "artifacts": artifact_names},
                        taskId=task_id,
                        contextId=context_id,
                    ),
                ),
            )
            await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())
        updater = TaskUpdater(event_queue, task_id, context_id)
        await updater.cancel(
            message=_agent_message("The LangGraph execution was canceled.", context_id, task_id)
        )


def build_app(settings: Settings) -> Any:
    card = agent_card(
        name=(
            "LangGraph NVIDIA Travel Fixture Agent"
            if settings.model_mode == "real"
            else "LangGraph LiteLLM Stub Travel Fixture Agent"
        ),
        description=(
            f"LangGraph A2A agent in {settings.model_mode} model mode using remote flight and "
            "hotel MCP fixture servers, A2A v1 routes, sideband events, and OpenTelemetry."
        ),
        base_url=settings.langgraph_base_url,
        rest_url=f"{settings.langgraph_base_url}/rest",
        sideband_uri=settings.sideband_uri,
        skills=[
            AgentSkill(
                id="fixture_flight_search",
                name="Fixture flight search",
                description=(
                    "Search simulated recurring flight records for a requested route and date."
                ),
                tags=["travel", "flights", "mcp", "fixture", settings.model_mode],
                examples=["Find flights from DEL to BOM on 2030-01-15 for 2 adults."],
                input_modes=["text/plain", "text/markdown", "application/json"],
                output_modes=["text/plain", "text/markdown"],
            ),
            AgentSkill(
                id="fixture_hotel_search",
                name="Fixture hotel search",
                description=(
                    "Search simulated hotel listings for a city and requested stay dates."
                ),
                tags=["travel", "hotels", "mcp", "fixture", settings.model_mode],
                examples=["Find hotels in Mumbai from 2030-01-15 to 2030-01-18."],
                input_modes=["text/plain"],
                output_modes=["text/plain"],
            ),
        ],
    )
    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(settings),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    app = FastAPI(title="LangGraph A2A Integration Agent", docs_url=None, redoc_url=None)
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(
            request_handler,
            rpc_url="/",
            enable_v0_3_compat=True,
        ),
        rest_routes=create_rest_routes(
            request_handler,
            path_prefix="/rest",
            enable_v0_3_compat=True,
        ),
    )
    return InvocationRateLimitMiddleware(
        app,
        enabled=settings.model_mode == "real" and settings.rate_limit_enabled,
        requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = load_settings()
    configure_telemetry("a2a-travel-agent-langgraph", __version__, settings.otlp_endpoint)
    # Framework-standard auto-instrumentation: the agent exports ordinary OpenInference
    # spans over OTLP and has no dependency on the Workbench or its normalization code.
    LangChainInstrumentor().instrument()
    app = instrument_asgi(build_app(settings))
    LOGGER.info("LangGraph Agent Card: %s/.well-known/agent-card.json", settings.langgraph_base_url)
    uvicorn.run(app, host=settings.host, port=settings.langgraph_port, log_level="info")


if __name__ == "__main__":
    main()

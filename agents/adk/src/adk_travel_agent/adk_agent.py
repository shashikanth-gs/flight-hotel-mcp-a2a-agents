from __future__ import annotations

import contextvars
import logging
from typing import Any

import uvicorn
from a2a.types import AgentSkill, TaskState
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.executor.config import A2aAgentExecutorConfig, ExecuteInterceptor
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from opentelemetry import context as otel_context
from opentelemetry import trace

from adk_travel_agent import __version__
from adk_travel_agent.cards import agent_card
from adk_travel_agent.config import Settings, load_settings
from adk_travel_agent.mcp_runtime import adk_mcp_toolsets
from adk_travel_agent.rate_limit import InvocationRateLimitMiddleware
from adk_travel_agent.sideband import sideband_event
from adk_travel_agent.stub_model import StubLiteLLMClient
from adk_travel_agent.telemetry import configure_telemetry, instrument_asgi

LOGGER = logging.getLogger(__name__)
_sideband_enabled: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "adk_sideband_enabled", default=False
)
_agent_span: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "adk_agent_span", default=None
)
_context_token: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "adk_context_token", default=None
)


def _metadata_event(uri: str, event: dict[str, Any]) -> dict[str, Any]:
    return {f"{uri}/events": [event]}


def _describe_adk_event(adk_event: Any) -> tuple[str, str, str, dict[str, Any] | None]:
    calls = adk_event.get_function_calls()
    if calls:
        names = [call.name for call in calls]
        return (
            "tool.started",
            "Tool invocation started",
            f"ADK requested: {', '.join(names)}",
            {"tools": names},
        )
    responses = adk_event.get_function_responses()
    if responses:
        names = [response.name for response in responses]
        return (
            "tool.completed",
            "Tool invocation completed",
            f"ADK received results from: {', '.join(names)}",
            {"tools": names},
        )
    if adk_event.is_final_response():
        return (
            "model.output",
            "Model response produced",
            "ADK produced its final model response.",
            None,
        )
    return "framework.event", "ADK execution event", "ADK advanced the agent execution.", None


def _interceptor(settings: Settings) -> ExecuteInterceptor:
    async def before_agent(request_context: Any) -> Any:
        enabled = settings.sideband_uri in request_context.requested_extensions
        _sideband_enabled.set(enabled)
        tracer = trace.get_tracer("real-agent-integration-lab.adk")
        span = tracer.start_span(
            "adk.agent.execute",
            attributes={
                "openinference.span.kind": "AGENT",
                "gen_ai.agent.name": "adk_travel_research_agent",
                "a2a.task.id": request_context.task_id or "",
                "a2a.context.id": request_context.context_id or "",
            },
        )
        _agent_span.set(span)
        _context_token.set(otel_context.attach(trace.set_span_in_context(span)))
        return request_context

    async def after_event(executor_context: Any, a2a_event: Any, adk_event: Any) -> Any:
        if not _sideband_enabled.get() or not hasattr(a2a_event, "metadata"):
            return a2a_event
        event_type, title, text, data = _describe_adk_event(adk_event)
        event = sideband_event(
            event_type,
            title,
            text=text if data is None else None,
            data=data,
            taskId=getattr(a2a_event, "task_id", None),
            contextId=getattr(a2a_event, "context_id", None),
        )
        a2a_event.metadata.update(_metadata_event(settings.sideband_uri, event))
        return a2a_event

    async def after_agent(executor_context: Any, terminal_event: Any) -> Any:
        if _sideband_enabled.get():
            state = TaskState.Name(terminal_event.status.state).removeprefix("TASK_STATE_").lower()
            terminal_event.metadata.update(
                _metadata_event(
                    settings.sideband_uri,
                    sideband_event(
                        "execution.completed",
                        "ADK execution completed",
                        text=f"ADK reached the terminal state: {state}.",
                        taskId=terminal_event.task_id,
                        contextId=terminal_event.context_id,
                    ),
                )
            )
        span = _agent_span.get()
        token = _context_token.get()
        if span is not None:
            span.set_attribute("a2a.task.state", TaskState.Name(terminal_event.status.state))
        if token is not None:
            otel_context.detach(token)
        if span is not None:
            span.end()
        _agent_span.set(None)
        _context_token.set(None)
        _sideband_enabled.set(False)
        return terminal_event

    return ExecuteInterceptor(
        before_agent=before_agent,
        after_event=after_event,
        after_agent=after_agent,
    )


def build_app(settings: Settings) -> Any:
    mcp_toolsets = adk_mcp_toolsets(settings)
    model = (
        LiteLlm(
            model="openai/a2a-fixture-stub",
            llm_client=StubLiteLLMClient(),
            temperature=0,
            max_tokens=2048,
            parallel_tool_calls=False,
        )
        if settings.model_mode == "stub"
        else LiteLlm(
            model=settings.model,
            temperature=0,
            max_tokens=2048,
            parallel_tool_calls=False,
        )
    )
    root_agent = LlmAgent(
        name=f"adk_travel_fixture_agent_{settings.model_mode}",
        description=("A travel fixture assistant with remote Flight and Hotel MCP tools."),
        model=model,
        instruction=(
            "/no_think\nYou are a concise A2A travel fixture agent. Use "
            "flights_search_flights for flight requests that include origin, destination, and a "
            "YYYY-MM-DD departure date. Use hotels_search_hotels for hotel requests that include "
            "a city, check-in date, and check-out date. Use the catalog tools when the user asks "
            "what routes, airports, or cities are supported. Ask for missing required fields. "
            "Invoke at most one MCP tool per request. Always include the relevant MCP result and "
            "state that schedules, availability, listings, and prices are simulated fixture data "
            "that cannot be booked. Never invent a result when an MCP tool returns no match."
        ),
        tools=mcp_toolsets,
    )
    card = agent_card(
        name=(
            "Google ADK NVIDIA Travel Fixture Agent"
            if settings.model_mode == "real"
            else "Google ADK LiteLLM Stub Travel Fixture Agent"
        ),
        description=(
            f"Google ADK A2A agent in {settings.model_mode} model mode using remote flight and "
            "hotel MCP fixture servers, streaming, sideband events, and OpenTelemetry."
        ),
        base_url=settings.adk_base_url,
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
                input_modes=["text/plain", "text/markdown"],
                output_modes=["text/markdown"],
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

    def executor_factory(runner: Any) -> A2aAgentExecutor:
        config = A2aAgentExecutorConfig(execute_interceptors=[_interceptor(settings)])
        return A2aAgentExecutor(runner=runner, config=config, force_new_version=True)

    app = to_a2a(
        root_agent,
        host=settings.host,
        port=settings.adk_port,
        agent_card=card,
        agent_executor_factory=executor_factory,
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
    configure_telemetry("a2a-travel-agent-adk", __version__, settings.otlp_endpoint)
    app = instrument_asgi(build_app(settings))
    LOGGER.info("ADK Agent Card: %s/.well-known/agent-card.json", settings.adk_base_url)
    uvicorn.run(app, host=settings.host, port=settings.adk_port, log_level="info")


if __name__ == "__main__":
    main()

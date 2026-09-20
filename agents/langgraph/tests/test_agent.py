from __future__ import annotations

import unittest
import warnings

from a2a.types import AgentSkill
from google.protobuf.json_format import MessageToDict
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from langgraph_travel_agent.cards import agent_card
from langgraph_travel_agent.config import Settings
from langgraph_travel_agent.intent import classify_request
from langgraph_travel_agent.langgraph_agent import _parse_json_object, _streamed_text, build_app
from langgraph_travel_agent.rate_limit import InvocationRateLimitMiddleware
from langgraph_travel_agent.sideband import extension_metadata, sideband_event
from langgraph_travel_agent.stub_model import stub_completion_spec


class LangGraphFixtureTests(unittest.TestCase):
    def test_limiter_covers_rest_invocations(self) -> None:
        async def endpoint(_request: object) -> JSONResponse:
            return JSONResponse({"status": "ok"})

        inner = Starlette(
            routes=[
                Route("/rest/message:send", endpoint, methods=["POST"]),
                Route("/rest/tasks/demo:cancel", endpoint, methods=["POST"]),
            ]
        )
        app = InvocationRateLimitMiddleware(inner, enabled=True, requests=1, window_seconds=60)
        with TestClient(app) as client:
            first = client.post("/rest/message:send")
            second = client.post("/rest/message:send")
            cancel = client.post("/rest/tasks/demo:cancel")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(cancel.status_code, 200)

    def test_intent_routing(self) -> None:
        self.assertEqual(classify_request("hi"), "conversation")
        self.assertEqual(classify_request("Plan three days in Kyoto."), "travel_plan")
        self.assertEqual(classify_request("What time is it in Tokyo?"), "time")
        self.assertEqual(classify_request("List the files in the workspace."), "filesystem")
        self.assertEqual(classify_request("Find flights from DEL to BOM"), "flight_search")
        self.assertEqual(classify_request("Find hotels in Mumbai"), "hotel_search")

    def test_stub_model_builds_dynamic_hotel_tool_call(self) -> None:
        spec = stub_completion_spec(
            [
                {
                    "role": "user",
                    "content": "Find hotels in Mumbai from 2030-01-15 to 2030-01-18",
                }
            ]
        )
        call = spec["mock_tool_calls"][0]["function"]
        self.assertEqual(call["name"], "hotels_search_hotels")
        self.assertIn('"check_out": "2030-01-18"', call["arguments"])

    def test_parsers_handle_streamed_text_and_json(self) -> None:
        from langchain_core.messages import AIMessageChunk

        self.assertEqual(
            _parse_json_object('```json\n{"city":"Kyoto"}\n```'),
            {"city": "Kyoto"},
        )
        self.assertEqual(_streamed_text(AIMessageChunk(content="Tokyo")), "Tokyo")
        self.assertEqual(
            _streamed_text(
                AIMessageChunk(
                    content="",
                    tool_call_chunks=[
                        {
                            "name": "flights_search_flights",
                            "args": "{}",
                            "id": "1",
                            "index": 0,
                        }
                    ],
                )
            ),
            "",
        )

    def test_sideband_is_opt_in(self) -> None:
        event = sideband_event(
            "graph.node.completed", "Graph node completed", data={"node": "plan"}
        )
        self.assertIsNone(extension_metadata("urn:test", False, event))
        self.assertEqual(
            extension_metadata("urn:test", True, event)["urn:test/events"][0]["type"],
            "graph.node.completed",
        )

    def test_agent_card_is_a2a_v1_with_rest(self) -> None:
        card = agent_card(
            name="Fixture",
            description="Fixture",
            base_url="http://127.0.0.1:4202",
            rest_url="http://127.0.0.1:4202/rest",
            sideband_uri="urn:test",
            skills=[AgentSkill(id="test", name="Test", description="Test", tags=["test"])],
        )
        payload = MessageToDict(card)
        self.assertEqual(len(payload["supportedInterfaces"]), 2)
        self.assertEqual(payload["supportedInterfaces"][1]["protocolBinding"], "HTTP+JSON")

    def test_langgraph_app_serves_agent_card_without_model_call(self) -> None:
        settings = Settings(
            nvidia_api_key="smoke-test-key",
            model="nvidia_nim/smoke-test-model",
            nvidia_api_base="https://integrate.api.nvidia.com/v1/",
            otlp_endpoint="http://127.0.0.1:6006/v1/traces",
            host="127.0.0.1",
            adk_port=4201,
            langgraph_port=4202,
            sideband_uri="urn:agent-observability:sideband-events:v1",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            app = build_app(settings)
        with TestClient(app) as client:
            response = client.get("/.well-known/agent-card.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "LangGraph NVIDIA Travel Fixture Agent")


if __name__ == "__main__":
    unittest.main()

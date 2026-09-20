from __future__ import annotations

import unittest
import warnings

from a2a.types import AgentSkill
from google.protobuf.json_format import MessageToDict
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from adk_travel_agent.adk_agent import build_app
from adk_travel_agent.cards import agent_card
from adk_travel_agent.config import Settings
from adk_travel_agent.mcp_runtime import mcp_server_urls
from adk_travel_agent.rate_limit import InvocationRateLimitMiddleware
from adk_travel_agent.sideband import extension_metadata, sideband_event
from adk_travel_agent.stub_model import stub_completion_spec


class AdkFixtureTests(unittest.TestCase):
    def test_limiter_blocks_only_new_agent_invocations(self) -> None:
        async def endpoint(_request: object) -> JSONResponse:
            return JSONResponse({"status": "ok"})

        inner = Starlette(routes=[Route("/", endpoint, methods=["POST"])])
        app = InvocationRateLimitMiddleware(inner, enabled=True, requests=1, window_seconds=60)
        with TestClient(app) as client:
            first = client.post("/", json={"method": "message/send"})
            second = client.post("/", json={"method": "message/stream"})
            task_read = client.post("/", json={"method": "tasks/get"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.headers["retry-after"], "60")
        self.assertEqual(task_read.status_code, 200)

    def test_remote_mcp_urls_are_configured(self) -> None:
        settings = self._settings()
        self.assertEqual(
            mcp_server_urls(settings),
            {
                "flights": "http://127.0.0.1:4301/mcp",
                "hotels": "http://127.0.0.1:4302/mcp",
            },
        )

    @staticmethod
    def _settings(**overrides: object) -> Settings:
        values = {
            "nvidia_api_key": "smoke-test-key",
            "model": "nvidia_nim/smoke-test-model",
            "nvidia_api_base": "https://integrate.api.nvidia.com/v1/",
            "otlp_endpoint": "http://127.0.0.1:6006/v1/traces",
            "host": "127.0.0.1",
            "adk_port": 4201,
            "langgraph_port": 4202,
            "sideband_uri": "urn:agent-observability:sideband-events:v1",
        }
        values.update(overrides)
        return Settings(**values)

    def test_stub_model_builds_dynamic_flight_tool_call(self) -> None:
        spec = stub_completion_spec(
            [{"role": "user", "content": "Find flights from DEL to BOM on 2030-01-15"}]
        )
        call = spec["mock_tool_calls"][0]["function"]
        self.assertEqual(call["name"], "flights_search_flights")
        self.assertIn('"departure_date": "2030-01-15"', call["arguments"])

    def test_sideband_is_opt_in(self) -> None:
        event = sideband_event("agent.completed", "Agent completed", text="ok")
        self.assertIsNone(extension_metadata("urn:test", False, event))
        self.assertEqual(
            extension_metadata("urn:test", True, event)["urn:test/events"][0]["type"],
            "agent.completed",
        )

    def test_agent_card_is_a2a_v1(self) -> None:
        card = agent_card(
            name="Fixture",
            description="Fixture",
            base_url="http://127.0.0.1:4201",
            sideband_uri="urn:test",
            skills=[AgentSkill(id="test", name="Test", description="Test", tags=["test"])],
        )
        payload = MessageToDict(card)
        self.assertEqual(payload["supportedInterfaces"][0]["protocolVersion"], "1.0")
        self.assertEqual(payload["capabilities"]["extensions"][0]["uri"], "urn:test")

    def test_adk_app_serves_agent_card_without_model_call(self) -> None:
        settings = self._settings()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            app = build_app(settings)
        with TestClient(app) as client:
            response = client.get("/.well-known/agent-card.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Google ADK NVIDIA Travel Fixture Agent")


if __name__ == "__main__":
    unittest.main()

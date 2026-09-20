from __future__ import annotations

import json
import re
from typing import Any

import litellm
from langchain_litellm import ChatLiteLLM

DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
FLIGHT_PATTERN = re.compile(
    r"\bfrom\s+(.+?)\s+to\s+(.+?)(?=\s+(?:on|for)\s+\d{4}-\d{2}-\d{2}\b|$)",
    re.IGNORECASE,
)
HOTEL_PATTERN = re.compile(
    r"\b(?:hotel|hotels|stay|stays)\s+in\s+(.+?)(?=\s+(?:from|on)\s+\d{4}-\d{2}-\d{2}\b|$)",
    re.IGNORECASE,
)


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


def _tool_result_text(content: Any) -> str:
    if isinstance(content, str):
        try:
            return _tool_result_text(json.loads(content))
        except json.JSONDecodeError:
            return content
    if isinstance(content, dict) and isinstance(content.get("structuredContent"), dict):
        return json.dumps(content["structuredContent"], ensure_ascii=False, indent=2)
    if isinstance(content, list) and content and isinstance(content[0], dict):
        first_text = content[0].get("text")
        if isinstance(first_text, str):
            return first_text
    return _text(content)


def _last_user_index(messages: list[dict[str, Any]]) -> int:
    for index in range(len(messages) - 1, -1, -1):
        if messages[index].get("role") == "user":
            return index
    return -1


def _tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "fixture-tool-call",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }


def stub_completion_spec(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Build deterministic LiteLLM mock arguments from the latest user turn."""
    user_index = _last_user_index(messages)
    if user_index < 0:
        return {"mock_response": "Stub agent is ready for a flight or hotel fixture search."}

    for message in messages[user_index + 1 :]:
        if message.get("role") in {"tool", "function"}:
            result = _tool_result_text(message.get("content", ""))
            return {
                "mock_response": (
                    "The stub LiteLLM used the requested MCP tool. Here is its deterministic "
                    f"fixture result:\n\n```json\n{result}\n```\n\nThis is simulated test data."
                )
            }

    query = _text(messages[user_index].get("content", "")).strip()
    dates = DATE_PATTERN.findall(query)
    lower_query = query.casefold()

    if "route" in lower_query and "list" in lower_query:
        return {
            "mock_response": "",
            "mock_tool_calls": [_tool_call("flights_list_routes", {})],
        }

    flight_match = FLIGHT_PATTERN.search(query)
    if flight_match and dates and ("flight" in lower_query or "fly" in lower_query):
        adults_match = re.search(r"\b(\d+)\s+adults?\b", query, re.IGNORECASE)
        return {
            "mock_response": "",
            "mock_tool_calls": [
                _tool_call(
                    "flights_search_flights",
                    {
                        "origin": flight_match.group(1).strip(),
                        "destination": flight_match.group(2).strip(),
                        "departure_date": dates[0],
                        "adults": int(adults_match.group(1)) if adults_match else 1,
                    },
                )
            ],
        }

    hotel_match = HOTEL_PATTERN.search(query)
    if hotel_match and len(dates) >= 2:
        guests_match = re.search(r"\b(\d+)\s+guests?\b", query, re.IGNORECASE)
        rooms_match = re.search(r"\b(\d+)\s+rooms?\b", query, re.IGNORECASE)
        return {
            "mock_response": "",
            "mock_tool_calls": [
                _tool_call(
                    "hotels_search_hotels",
                    {
                        "city": hotel_match.group(1).strip(),
                        "check_in": dates[0],
                        "check_out": dates[1],
                        "guests": int(guests_match.group(1)) if guests_match else 1,
                        "rooms": int(rooms_match.group(1)) if rooms_match else 1,
                    },
                )
            ],
        }

    return {
        "mock_response": (
            "This is the deterministic LiteLLM stub. Try `Find flights from DEL to BOM on "
            "2030-01-15 for 2 adults` or `Find hotels in Mumbai from 2030-01-15 to "
            "2030-01-18 for 2 guests`."
        )
    }


class StubChatLiteLLM(ChatLiteLLM):
    async def acompletion_with_retry(self, run_manager: Any = None, **kwargs: Any) -> Any:
        messages = kwargs.get("messages", [])
        kwargs.update(stub_completion_spec(messages))
        kwargs["model"] = "openai/a2a-fixture-stub"
        kwargs["api_key"] = "fixture-key"
        return await litellm.acompletion(**kwargs)

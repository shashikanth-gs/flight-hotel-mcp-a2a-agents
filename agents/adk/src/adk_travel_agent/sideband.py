from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from adk_travel_agent.telemetry import current_trace_references


def sideband_event(
    event_type: str,
    title: str,
    *,
    text: str | None = None,
    data: Any | None = None,
    level: str = "info",
    **references: str | None,
) -> dict[str, Any]:
    """Build one event in the lab's explicitly provisional sideband contract."""
    event: dict[str, Any] = {
        "type": event_type,
        "title": title,
        "level": level,
        "timestamp": datetime.now(UTC).isoformat(),
        **current_trace_references(),
        **{key: value for key, value in references.items() if value},
    }
    if data is not None:
        event["parts"] = [{"data": data, "mediaType": "application/json"}]
    elif text is not None:
        event["parts"] = [{"text": text, "mediaType": "text/plain"}]
    return event


def extension_metadata(uri: str, enabled: bool, *events: dict[str, Any]) -> dict[str, Any] | None:
    if not enabled or not events:
        return None
    return {f"{uri}/events": list(events)}

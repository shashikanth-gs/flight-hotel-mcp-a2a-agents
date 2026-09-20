from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIRECTORY = Path(__file__).resolve().parents[2]
DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/"
DEFAULT_OTLP_ENDPOINT = "http://127.0.0.1:6006/v1/traces"
DEFAULT_SIDEBAND_URI = "urn:agent-observability:sideband-events:v1"
DEFAULT_FLIGHT_MCP_URL = "http://127.0.0.1:4301/mcp"
DEFAULT_HOTEL_MCP_URL = "http://127.0.0.1:4302/mcp"


@dataclass(frozen=True)
class Settings:
    nvidia_api_key: str
    model: str
    nvidia_api_base: str
    otlp_endpoint: str
    host: str
    adk_port: int
    langgraph_port: int
    sideband_uri: str
    model_mode: str = "real"
    flight_mcp_url: str = DEFAULT_FLIGHT_MCP_URL
    hotel_mcp_url: str = DEFAULT_HOTEL_MCP_URL
    adk_public_base_url: str = ""
    langgraph_public_base_url: str = ""
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 1
    rate_limit_window_seconds: int = 60

    @property
    def adk_base_url(self) -> str:
        return self.adk_public_base_url or f"http://{self.host}:{self.adk_port}"

    @property
    def langgraph_base_url(self) -> str:
        return self.langgraph_public_base_url or f"http://{self.host}:{self.langgraph_port}"


def _port(name: str, fallback: int) -> int:
    value = int(os.getenv(name, str(fallback)))
    if not 1 <= value <= 65535:
        raise ValueError(f"{name} must be between 1 and 65535.")
    return value


def load_settings(*, require_credentials: bool = True) -> Settings:
    load_dotenv(ROOT_DIRECTORY / ".env", override=False)
    model_mode = os.getenv("AGENT_MODEL_MODE", "real").strip().casefold()
    if model_mode not in {"real", "stub"}:
        raise ValueError("AGENT_MODEL_MODE must be real or stub.")
    api_key = os.getenv("NVIDIA_NIM_API_KEY", "").strip()
    model = os.getenv("NVIDIA_MODEL", "").strip()
    if require_credentials and model_mode == "real" and not api_key:
        raise ValueError(f"NVIDIA_NIM_API_KEY is missing. Add it to {ROOT_DIRECTORY / '.env'}.")
    if (
        require_credentials
        and model_mode == "real"
        and (not model or model.endswith("replace-with-your-model-id"))
    ):
        raise ValueError(
            f"NVIDIA_MODEL is missing. Add the LiteLLM model ID to {ROOT_DIRECTORY / '.env'}."
        )
    if model_mode == "real" and model and not model.startswith("nvidia_nim/"):
        raise ValueError("NVIDIA_MODEL must use LiteLLM's nvidia_nim/ provider prefix.")

    settings = Settings(
        nvidia_api_key=api_key,
        model=model,
        nvidia_api_base=os.getenv("NVIDIA_NIM_API_BASE", DEFAULT_NVIDIA_BASE_URL).strip(),
        otlp_endpoint=os.getenv(
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", DEFAULT_OTLP_ENDPOINT
        ).strip(),
        host=os.getenv("AGENT_HOST", "127.0.0.1").strip(),
        adk_port=_port("ADK_AGENT_PORT", 4201),
        langgraph_port=_port("LANGGRAPH_AGENT_PORT", 4202),
        sideband_uri=os.getenv("SIDEBAND_EXTENSION_URI", DEFAULT_SIDEBAND_URI).strip(),
        model_mode=model_mode,
        flight_mcp_url=os.getenv("FLIGHT_MCP_URL", DEFAULT_FLIGHT_MCP_URL).strip(),
        hotel_mcp_url=os.getenv("HOTEL_MCP_URL", DEFAULT_HOTEL_MCP_URL).strip(),
        adk_public_base_url=os.getenv("ADK_PUBLIC_BASE_URL", "").strip().rstrip("/"),
        langgraph_public_base_url=os.getenv("LANGGRAPH_PUBLIC_BASE_URL", "").strip().rstrip("/"),
        rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "false").strip().casefold()
        in {"1", "true", "yes", "on"},
        rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "1")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
    )
    if settings.rate_limit_requests < 1:
        raise ValueError("RATE_LIMIT_REQUESTS must be at least 1.")
    if settings.rate_limit_window_seconds < 1:
        raise ValueError("RATE_LIMIT_WINDOW_SECONDS must be at least 1.")
    # LiteLLM's NVIDIA provider reads these canonical environment variables.
    os.environ["NVIDIA_NIM_API_KEY"] = settings.nvidia_api_key
    os.environ["NVIDIA_NIM_API_BASE"] = settings.nvidia_api_base
    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental")
    return settings

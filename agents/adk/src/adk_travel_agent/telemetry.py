from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode


def configure_telemetry(service_name: str, service_version: str, endpoint: str) -> None:
    if not endpoint:
        return
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "deployment.environment.name": "local-integration",
            }
        )
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)


def instrument_asgi(app: Any) -> Any:
    """Wrap an ASGI app so incoming W3C trace context becomes the active parent."""
    return OpenTelemetryMiddleware(app)


def current_trace_references() -> dict[str, str]:
    context = trace.get_current_span().get_span_context()
    if not context.is_valid:
        return {}
    return {"traceId": f"{context.trace_id:032x}", "spanId": f"{context.span_id:016x}"}


@contextmanager
def traced_span(kind: str, name: str, attributes: dict[str, Any] | None = None) -> Iterator[Any]:
    tracer = trace.get_tracer("real-agent-integration-lab")
    with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
        span.set_attribute("openinference.span.kind", kind.upper())
        for key, value in (attributes or {}).items():
            if value is not None:
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as error:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            raise

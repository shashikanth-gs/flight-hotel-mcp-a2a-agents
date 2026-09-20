# Framework compatibility notes

## Supported Python

The packages declare Python 3.11 and newer. CI exercises Python 3.11 through 3.14. Container
images use Python 3.12 as the conservative deployment baseline.

## MCP SDK versions

The MCP servers use the official MCP Python SDK 2.x. The ADK and LangGraph packages currently pin
the MCP 1.x client because their framework adapters require that API generation. Streamable HTTP
negotiation allows those clients to communicate with the server implementation.

Keep the three applications in separate environments. Do not combine their dependencies into one
virtual environment without first resolving the SDK constraints.

## Google ADK

Google ADK currently labels parts of its A2A conversion layer as experimental. It may emit
experimental-feature warnings during startup and requests. The public A2A protocol and the
standalone A2A SDK are not made experimental by this framework warning.

## LangGraph stub mode

With the pinned LiteLLM and LangChain integration, stub-mode graph execution may emit Pydantic
serializer warnings while mock generations pass through graph streaming internals. The A2A task
still completes and returns the expected artifact. Real-model streaming does not use this mock
generation path.

These caveats are kept visible rather than globally suppressing upstream warnings. Revisit the
pins through a tested dependency update when the adapters remove the underlying limitations.

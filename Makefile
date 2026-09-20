.PHONY: install lock lint format format-check test check compose-check clean

PROJECTS := mcp-servers agents/adk agents/langgraph

install:
	uv sync --project mcp-servers --locked
	uv sync --project agents/adk --locked
	uv sync --project agents/langgraph --locked

lock:
	uv lock --project mcp-servers
	uv lock --project agents/adk
	uv lock --project agents/langgraph

lint:
	uv run --project mcp-servers ruff check mcp-servers/src mcp-servers/tests
	uv run --project agents/adk ruff check agents/adk/src agents/adk/tests
	uv run --project agents/langgraph ruff check agents/langgraph/src agents/langgraph/tests

format:
	uv run --project mcp-servers ruff format mcp-servers/src mcp-servers/tests
	uv run --project agents/adk ruff format agents/adk/src agents/adk/tests
	uv run --project agents/langgraph ruff format agents/langgraph/src agents/langgraph/tests

format-check:
	uv run --project mcp-servers ruff format --check mcp-servers/src mcp-servers/tests
	uv run --project agents/adk ruff format --check agents/adk/src agents/adk/tests
	uv run --project agents/langgraph ruff format --check agents/langgraph/src agents/langgraph/tests

test:
	uv run --project mcp-servers python -m unittest discover -s mcp-servers/tests -v
	uv run --project agents/adk python -m unittest discover -s agents/adk/tests -v
	uv run --project agents/langgraph python -m unittest discover -s agents/langgraph/tests -v

compose-check:
	docker compose config --quiet

check: lint format-check test compose-check

clean:
	rm -rf mcp-servers/.venv agents/adk/.venv agents/langgraph/.venv
	rm -rf mcp-servers/build agents/adk/build agents/langgraph/build
	rm -rf .ruff_cache mcp-servers/.ruff_cache agents/adk/.ruff_cache agents/langgraph/.ruff_cache
	rm -rf mcp-servers/src/*.egg-info agents/adk/src/*.egg-info agents/langgraph/src/*.egg-info
	rm -rf mcp-servers/src/travel_mcp/__pycache__ mcp-servers/tests/__pycache__
	rm -rf agents/adk/src/adk_travel_agent/__pycache__ agents/adk/tests/__pycache__
	rm -rf agents/langgraph/src/langgraph_travel_agent/__pycache__ agents/langgraph/tests/__pycache__

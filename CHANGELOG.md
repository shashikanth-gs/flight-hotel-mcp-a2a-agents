# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Open-source governance, contribution, security, support, and deployment documentation.
- Exact fixture dataset coverage, date semantics, and unsupported-query documentation.
- Docker Hub publication workflow for multi-platform MCP, ADK, and LangGraph images.
- GitHub README image links, status badges, and copy-ready Docker Hub Overview documentation.
- Helm chart for hardened Kubernetes deployment of MCP and A2A stub or real services.
- Reproducible uv lock files and automated CI checks.
- Hardened non-root container images and Compose health checks.

### Changed

- Promoted the interoperability playground to the repository root.
- Organized framework implementations under `agents/adk` and `agents/langgraph`.
- Renamed Python import packages to avoid the ambiguous `agent_lab` name.
- Removed obsolete demos, generated environments, and legacy Node MCP artifacts.

## [0.2.0] - 2026-09-11

### Added

- Flight and hotel MCP fixture services over Streamable HTTP.
- Google ADK and LangGraph A2A agents.
- Real NVIDIA NIM and deterministic LiteLLM stub modes.
- Real-mode invocation rate limiting and optional OpenTelemetry export.
- Deterministic airport, flight, and hotel fixture catalogs.

# Publishing container images

GitHub Actions publishes three public image repositories to Docker Hub:

| Image | Purpose | Runtime variants |
|---|---|---|
| `<namespace>/flight-hotel-mcp-server` | Standalone flight and hotel MCP servers | `flight-mcp` or `hotel-mcp` command |
| `<namespace>/flight-hotel-a2a-adk` | Google ADK A2A agent | Real or stub mode through environment variables |
| `<namespace>/flight-hotel-a2a-langgraph` | LangGraph A2A agent | Real or stub mode through environment variables |

The MCP image intentionally omits the `a2a-` prefix because it works with any Streamable HTTP MCP
client. The agent images retain the prefix because their public interface is A2A. One MCP image is
sufficient because the flight and hotel services share code and fixture data but use separate
entry-point commands. Real and stub agents also share an image per framework because their mode is
selected at runtime.

## Docker Hub setup

1. Create the three public repositories listed above in the intended Docker Hub namespace.
2. Create a Docker Hub personal access token with read and write permission.
3. Add the following to the GitHub repository's **Settings → Secrets and variables → Actions**:
   - Repository variable `DOCKERHUB_USERNAME`: the user that owns the access token.
   - Repository variable `DOCKERHUB_NAMESPACE`: the user or organization that owns the images.
     For a personal namespace, use the same value as `DOCKERHUB_USERNAME`.
   - Repository secret `DOCKERHUB_TOKEN`: the personal access token; do not store a password.
4. The workflow updates each repository's short description and Overview from its package README
   after the corresponding image is pushed successfully.

The workflow never passes the NVIDIA API key into an image build, so model credentials are not
included in published images.

## Publication policy

The [publish workflow](../.github/workflows/publish-containers.yml) builds both `linux/amd64` and
`linux/arm64` images.

| Git event | Published tags |
|---|---|
| Push to `main` | `main` and `sha-<commit>` |
| Tag such as `v1.2.3` | `1.2.3`, `1.2`, `1`, `latest`, and `sha-<commit>` |
| Manual workflow run | `sha-<commit>` plus any tag derived from its Git ref |

Release tags should follow Semantic Versioning. A normal release is:

```bash
git tag -s v1.2.3 -m "v1.2.3"
git push origin v1.2.3
```

The existing CI workflow continues to build every container on pull requests without publishing
it. Only trusted pushes, version tags, and manual runs can reach the publishing workflow.

## Pulling images

To pull the current default-branch builds, replace `<namespace>` with the configured Docker Hub
namespace:

```bash
docker pull <namespace>/flight-hotel-mcp-server:main
docker pull <namespace>/flight-hotel-a2a-adk:main
docker pull <namespace>/flight-hotel-a2a-langgraph:main
```

The `latest` tag is created with a versioned release. For repeatable deployments, pin a version tag
or image digest instead of `main` or `latest`.

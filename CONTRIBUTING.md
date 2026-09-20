# Contributing

Thank you for helping improve the A2A Travel Playground. Contributions of protocol compatibility
fixes, framework examples, tests, documentation, and clearly simulated fixture data are welcome.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before opening a change

- Search existing issues and pull requests.
- Open an issue before a large architectural change.
- Keep changes focused on an interoperability or learning outcome.
- Never include credentials, personal data, scraped commercial data, or live booking claims.

Small fixes and documentation improvements can go directly to a pull request.

## Development setup

Install Python 3.11 or newer, uv, and Docker with Compose v2. Then run:

```bash
make install
make check
```

The three Python packages intentionally use separate lock files and environments. After changing a
dependency in one `pyproject.toml`, run `uv lock --project <package-directory>` and commit the
updated lock file.

## Code expectations

- Add or update tests for behavioral changes.
- Use type annotations for new public Python functions.
- Keep protocol and transport concerns separate from fixture-domain logic.
- Keep real and stub behavior in the same framework package.
- Keep sample responses explicit that inventory and prices are simulated.
- Run `make format` and `make check` before submitting.
- Update public documentation and the changelog when behavior changes.

## Pull requests

A pull request should explain:

- The problem or interoperability scenario
- The chosen approach and important tradeoffs
- How the change was tested
- Any security, compatibility, configuration, or data implications

Maintainers may ask to split unrelated work. Reviews focus on correctness, protocol behavior,
operational safety, readability, and whether another contributor can reproduce the result.

## Commit messages

Use short, imperative subjects such as `Add hotel city aliases` or
`Fix ADK streaming completion`. Conventional Commits are welcome but not required.

## Licensing

Unless explicitly stated otherwise, contributions submitted to this repository are licensed under
the [Apache License 2.0](LICENSE), consistent with the project's license.

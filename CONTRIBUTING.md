# Contributing to Pi Agent for Python

Thanks for helping improve the project. Keep changes small, testable, and inside the
existing three-layer design:

```text
pi_ai      provider and streaming primitives
pi_agent   reusable agent loop, tools, events, and sessions
pi_coding  CLI, TUI, configuration, resources, and extensions
```

`pi_agent` must remain independent of the CLI, Textual, Rich, and application-specific
filesystem paths.

## Development

Install the locked development environment and run the CLI from the checkout:

```bash
uv sync --dev --locked
uv run pi-agent --version
uv run pi-agent --help
```

Before opening a pull request, run:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv build
```

Add focused regression coverage for behavior changes. Agent-loop tests should use fake
providers and tools; tests must not require API credentials or network access.

## Pull requests

Explain the motivation, observable behavior change, and checks you ran. Include a
screenshot for TUI changes when it helps review. Keep unrelated refactors in separate
pull requests.

Provider/model catalog changes belong in `src/pi_coding/data/catalog.toml`. User-facing
behavior belongs in both READMEs and, when relevant, the packaged reference docs under
`src/pi_coding/data/docs/`.

Security reports do not belong in public issues. Follow [SECURITY.md](SECURITY.md).

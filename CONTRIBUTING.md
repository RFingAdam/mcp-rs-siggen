# Contributing to mcp-rs-siggen

Thank you for your interest in contributing! This guide will help you get started.
## Before you contribute

By submitting a pull request to this repository, you agree to the terms
of [CLA.md](CLA.md) — a short contributor license agreement that lets the
Maintainer offer this Project under both its default open license and a
separate paid commercial license (see [COMMERCIAL.md](COMMERCIAL.md)),
without needing to track down every past contributor individually every
time that offering changes. You keep your own copyright; you're just
granting the Maintainer the same relicensing rights over your
contribution that they already have over the rest of the codebase.

No signature or bot step is required today — opening the PR is the
agreement. Read CLA.md before you submit if you want the full terms.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RFingAdam/mcp-rs-siggen.git
   cd mcp-rs-siggen
   ```

2. **Install [uv](https://docs.astral.sh/uv/) (recommended):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies:**
   ```bash
   uv sync --dev
   ```

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=rs_siggen_mcp --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_tools.py -v
```

## Code Quality

```bash
# Lint
uv run ruff check src/ tests/

# Auto-fix lint issues
uv run ruff check --fix src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run mypy src/rs_siggen_mcp/
```

## Code Style

- Python 3.10+ syntax (use `X | Y` union types, not `Union[X, Y]`)
- Line length: 100 characters
- Ruff rules: E, F, I, N, W, UP
- Type annotations on all public functions
- Docstrings on modules and public functions

## Adding a New Tool

1. **Choose or create a handler module** in `src/rs_siggen_mcp/tools/` (e.g., `_rf_output.py`)

2. **Add the handler function:**
   ```python
   async def handle_my_tool(
       arguments: dict[str, Any], host: str | None, port: int | None
   ) -> CallToolResult:
       sg = await _common._get_siggen(host, port)
       result = await sg.some_method(arguments["param"])
       return _common._format_result({"status": "ok", "value": result})
   ```

3. **Add the Tool definition** to the module's `get_tools()` function

4. **Register the handler** in the module's `*_HANDLERS` dict

5. **Import in `__init__.py`** if creating a new module:
   - Import the handlers dict and `get_tools` function
   - Add to `_ALL_HANDLERS`
   - Add to `get_tools()` aggregation

6. **Write tests** in `tests/` following existing patterns (mock the driver, test through `handle_tool`)

## Pull Request Process

1. Fork the repository and create a feature branch
2. Make your changes with tests
3. Ensure all checks pass: `uv run pytest && uv run ruff check src/ tests/ && uv run mypy src/rs_siggen_mcp/`
4. Submit a PR with a clear description of changes
5. Link any related issues

## Reporting Issues

Use [GitHub Issues](https://github.com/RFingAdam/mcp-rs-siggen/issues) with the provided templates for bug reports and feature requests.

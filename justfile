default: serve

serve:
    uv run python -m comfyops_mcp.server

dev:
    uv run python -m comfyops_mcp.server

frontend:
    cd web_sota && npm run dev

test:
    uv run pytest tests/ -q

lint:
    uv run ruff check src/ tests/

fmt:
    uv run ruff format src/ tests/

clean:
    uv run ruff check src/ tests/ && uv run ruff format src/ tests/

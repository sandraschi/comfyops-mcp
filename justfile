set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default: dev

# --- Dev ---

serve:
    uv run python -m comfyops_mcp.server

dev:
    uv run python -m comfyops_mcp.server

frontend:
    cd web_sota && npx vite --port 11088

http:
    uv run python -m comfyops_mcp.server

# --- Testing ---

test:
    uv run pytest tests/ -q

lint:
    uv run ruff check src/ tests/

fmt:
    uv run ruff format src/ tests/

clean:
    uv run ruff check src/ tests/ && uv run ruff format src/ tests/

types:
    cd web_sota && npx tsc --noEmit

lint-green:
    uv run ruff check src/ tests/ --fix
    uv run ruff format src/ tests/

types-green:
    cd web_sota && npx tsc --noEmit

gates-green: lint-green types-green test

ci: lint test types

# --- Screenshots ---

screenshots:
    cd web_sota && npx playwright test --project=screenshots

# --- Sync ---

sync-deps:
    uv sync && cd web_sota && npm install

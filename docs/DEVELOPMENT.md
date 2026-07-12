# Development

## Setup

```powershell
uv sync
uv run pre-commit install
```

## Commands

```powershell
just dev       # Run the MCP server (stdio)
just test      # Run pytest
just lint      # Ruff check
just fmt       # Ruff format
```

## Project Structure

```
comfyops-mcp/
├── src/comfyops_mcp/
│   ├── server.py              # FastMCP app + tool registrations
│   ├── config.py              # Env var config
│   ├── comfyui_manager.py     # ComfyUI API client + sidecar lifecycle
│   └── tools/
│       ├── generate.py        # comfy_generate portmanteau
│       ├── workflows.py       # comfy_workflows portmanteau
│       ├── models_tool.py     # comfy_models portmanteau
│       ├── library.py         # comfy_library portmanteau
│       ├── agentic.py         # comfy_agentic_assist
│       └── prefab/cards.py    # Prefab UI cards
├── workflows/                 # Curated ComfyUI workflow JSONs
├── web_sota/                  # Vite + React dashboard
└── tests/                     # pytest suite
```

## Adding a Workflow

1. Export your workflow JSON from ComfyUI (Save As → workflow.json)
2. Add `_meta` block with name, description, model_type, and params
3. Place in `workflows/{your-id}.json`
4. Add a `workflows/{your-id}.md` sidecar with human-readable docs
5. Add VRAM estimate to `_MODEL_VRAM_MAP` in `tools/generate.py`
6. Add a test in `tests/test_tools.py`

## Adding a Tool

A new tool module in `tools/` needs:
1. A `register_tools(mcp: FastMCP)` function with `@mcp.tool()` decorators
2. Import in `server.py` `register_tools()`
3. Tests in `tests/`
4. Entry in `docs/TOOLS.md`

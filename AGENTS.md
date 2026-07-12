# AGENTS.md — comfyops-mcp

## Identity
- **Name**: comfyops-mcp
- **Purpose**: Local generative AI engine — wraps ComfyUI for image/video/upscale/inpaint
- **Stack**: FastMCP 3.2+, httpx, SQLite3, comfyui_manager
- **Ports**: 11086 (ComfyUI), 11087 (backend), 11088 (frontend)
- **Transports**: stdio and streamable HTTP

## Key Files

| File | Purpose |
|------|---------|
| `src/comfyops_mcp/server.py` | FastMCP app + tool registration |
| `src/comfyops_mcp/comfyui_manager.py` | ComfyUI sidecar lifecycle + API client |
| `src/comfyops_mcp/config.py` | Env var config |
| `src/comfyops_mcp/tools/generate.py` | comfy_generate portmanteau |
| `src/comfyops_mcp/tools/workflows.py` | comfy_workflows portmanteau |
| `src/comfyops_mcp/tools/models_tool.py` | comfy_models portmanteau |
| `src/comfyops_mcp/tools/library.py` | comfy_library portmanteau |
| `src/comfyops_mcp/tools/agentic.py` | comfy_agentic_assist |
| `src/comfyops_mcp/tools/prefab/cards.py` | Prefab UI cards |
| `workflows/` | Curated ComfyUI workflow JSONs |
| `web_sota/` | Vite + React dashboard |

## Tools

| Tool | Ops | Notes |
|------|-----|-------|
| comfy_generate | image, video, upscale, inpaint, edit | Submits workflow JSON, polls result |
| comfy_workflows | list, get, validate, register | Curated workflow depot |
| comfy_models | list_installed, check_vram, health | VRAM check before queueing |
| comfy_library | recent, search, record | SQLite generation history |
| comfy_agentic_assist | — | SEP-1577 sampling for multi-step gen |

## Quick Ref
```
uv run python -m comfyops_mcp.server           # stdio
.\start.ps1                                      # full stack
```

## Danger Zones
- comfy_generate can saturate the GPU for 30-300s — vram_guard prevents OOM
- Workflows execute arbitrary ComfyUI node graphs — trust curated workflows only
- ComfyUI must be installed at COMFYOPS_COMFYUI_DIR (or connected remotely)

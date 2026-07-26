# Onboarding — comfyops-mcp

## What this is for

**comfyops-mcp** drives a local [ComfyUI](https://github.com/comfyanonymous/ComfyUI) install so agents and the dashboard can generate images/video without the node editor.

It does **not** browse or download marketplace models. Use **[civitai-mcp](../../civitai-mcp)** (ports 11124/11125) to search/download into your ComfyUI models tree, then generate here.

## Cost / hardware

| Question | Answer |
|----------|--------|
| Cloud fees? | None — fully local |
| GPU? | NVIDIA recommended (VRAM guard checks free memory) |
| Disk? | Models are multi‑GB; point `COMFYOPS_MODELS_DIR` at ComfyUI’s `models/` |
| Money? | Electricity + your own weights (licenses vary) |

## Setup

1. Install ComfyUI (typical: `D:\ComfyUI`) and confirm it boots.
2. Put at least one checkpoint under `models/checkpoints/` (or use civitai-mcp depot pin).
3. In this repo:

```powershell
cd D:\Dev\repos\comfyops-mcp
Copy-Item .env.example .env
# Edit: COMFYOPS_COMFYUI_DIR, COMFYOPS_MODELS_DIR, ports if needed
uv sync
.\start.bat
```

4. Open dashboard: http://127.0.0.1:11088  
   Backend health: http://127.0.0.1:11087/api/health  
   ComfyUI API: http://127.0.0.1:11086 (default)

Fleet launcher (from anywhere):

```powershell
D:\Dev\repos\mcp-central-docs\starts\comfyops-mcp-start.bat
```

## Ports

| Port | Role |
|------|------|
| 11086 | ComfyUI sidecar |
| 11087 | FastMCP / REST backend |
| 11088 | Vite dashboard (`web_sota/`) |

## Pitfalls

- **ComfyUI offline** → dashboard shows red onboarding; generation tools fail until sidecar is up
- **Empty models dir** → workflows queue but fail; fill via civitai-mcp or manual download
- **Wrong models path** — ComfyUI only loads from its own `models/` tree; keep `COMFYOPS_MODELS_DIR` aligned
- **VRAM** — large FLUX/Wan jobs need free VRAM; check `comfy_models` / health KPIs first

## Related docs

- [CONFIGURATION.md](CONFIGURATION.md) — env vars
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — common failures
- [TOOLS.md](TOOLS.md) — MCP portmanteau ops

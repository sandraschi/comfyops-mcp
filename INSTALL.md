# Installation

## Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)** (`winget install Astral.uv`)
- **Node.js 18+** (for web dashboard, optional)
- **ComfyUI** at `D:\ComfyUI` (or set `COMFYOPS_COMFYUI_DIR`) — optional but required for generation

## Quick Start

```powershell
git clone https://github.com/sandraschi/comfyops-mcp
cd comfyops-mcp
uv sync
.\start.ps1
```

This starts the backend on :11087 and the dashboard on :11088, then opens your browser.

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "comfyops": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/comfyops-mcp", "run", "python", "-m", "comfyops_mcp.server"]
    }
  }
}
```

## Dashboard Only (no ComfyUI)

```powershell
cd web_sota
npm install
npm run dev -- --port 11088
```

Browse workflows, models, and the generation library. Generation requires ComfyUI to be running — `comfy_models/health` will show the connection status.

## ComfyUI Setup

1. Download ComfyUI from [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
2. Install to `D:\ComfyUI` (or set `COMFYOPS_COMFYUI_DIR` in `.env`)
3. Download models to `D:\models\comfyui\` (or set `COMFYOPS_MODELS_DIR`)
4. Run `.\start.ps1` — comfyops detects and launches ComfyUI automatically

## Verify Installation

```powershell
uv run python -m comfyops_mcp.server
# In another terminal:
uv run python -c "
import asyncio, httpx
async def test():
    r = await httpx.AsyncClient().get('http://127.0.0.1:11087/health')
    print(r.json())
asyncio.run(test())
"
```

# comfyops-mcp — Local Generative AI Engine

**FastMCP 3.2** — Wraps ComfyUI for image, video, upscale, and inpaint generation on RTX 4090.

| Item | Details |
|------|---------|
| **Status** | v0.1.0 — MVP |
| **Ports** | ComfyUI **11086**, Backend **11087**, Dashboard **11088** |
| **Stack** | FastMCP 3.2, ComfyUI API, SQLite3, Vite/React/Tailwind |
| **Depends on** | ComfyUI (optional), model weights |

## Quick Start

```bash
git clone https://github.com/sandraschi/comfyops-mcp
cd comfyops-mcp
uv sync
.\start.ps1
```

## Tools

### comfy_generate
Generate images, videos, upscales, inpaints, and edits via curated ComfyUI workflows.

### comfy_workflows
Manage the workflow depot — list available workflows, get details, validate JSON, register new ones.

### comfy_models
List installed model checkpoints, check GPU VRAM, get ComfyUI health status.

### comfy_library
Browse past generations with search and recording.

### comfy_agentic_assist
Multi-step agentic generation planning via MCP sampling (SEP-1577).

## Model Roster

| Model | Type | VRAM | License |
|-------|------|------|---------|
| FLUX.2 [klein] | Image | ~6 GB | Apache 2.0 |
| SDXL | Image | ~5.5 GB | MIT |
| Wan 2.2 | Video | ~20 GB | Apache 2.0 |
| ESRGAN | Upscale | ~2 GB | MIT |

## VRAM Management

The 24 GB RTX 4090 is shared with Ollama/LM Studio. The `vram_guard` checks free VRAM before queueing and refuses jobs that cannot fit.

## Dashboard

Vite + React + Tailwind webapp with pages for Dashboard, Generate, Gallery, Workflows, and Models.

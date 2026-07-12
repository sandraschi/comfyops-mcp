# comfyops-mcp — Local Generative AI Engine

Wraps ComfyUI so you can generate images, video, and upscales from a prompt — without ever touching the node editor. Pick a curated workflow, type what you want, get a PNG or MP4.

**FastMCP 3.2** | 5 portmanteau tools | 6 curated workflows | ComfyUI :11086 | Backend :11087 | Dashboard :11088

<p align="center">
  <img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/badge/status-MVP-orange?style=flat-square" alt="Status">
</p>

## Preview

ComfyUI is the industry standard for local AI generation — but its node editor is a wall of patch cables. comfyops-mcp hides all of that behind a simple `comfy_generate(workflow_id, prompt)` call.

| ComfyUI Node Editor (what we wrap) | comfyops Dashboard (what you see) |
|------------------------------------|-----------------------------------|
| ![ComfyUI](docs/screenshots/comfyui-node-editor.png) | ![Dashboard](docs/screenshots/dashboard.png) |

> Screenshots pending — run `just screenshots` once the dashboard is live.

## What You Can Do

```
"Generate a 1024x1024 image of a cat surfing on a pizza slice"
"Upscale my archive of 2024 SD generations to 4K"
"Turn this photo into a cinematic video" (Wan 2.2 i2v)
"Make 10 variations of this character concept"
```

## Quick Install

```powershell
git clone https://github.com/sandraschi/comfyops-mcp
cd comfyops-mcp
uv sync
.\start.ps1
```

See [INSTALL.md](INSTALL.md) for prerequisites and Claude Desktop config.

## Features

- **Prompt-to-image**: FLUX.2 klein, SDXL, Z-Image Turbo — curated workflows with sensible defaults
- **Prompt-to-video**: Wan 2.2 (quality) and LTX-Video (speed)
- **Upscale & restore**: ESRGAN and SUPIR for archive restoration
- **Inpaint & edit**: Region-based editing via FLUX.2
- **VRAM guard**: Checks free GPU memory before queueing — no OOM crashes
- **Seed control**: Same seed + same workflow = identical output, every time
- **Generation library**: SQLite history with search — browse past prompts and seeds
- **Agentic workflow**: Multi-step generation planning via MCP sampling (SEP-1577)
- **Prefab cards**: Rich in-chat status and generation cards

## How It Runs

| Mode | ComfyUI required? | When |
|------|--------------------|------|
| MCP tools (stdio/HTTP) | Yes | Generation via Claude Desktop, Cursor, opencode |
| Dashboard (Vite) | No | Browse workflows, models, library — generation needs ComfyUI |
| ComfyUI sidecar | Optional | `start.ps1` can launch ComfyUI automatically if `COMFYOPS_COMFYUI_DIR` is set |

## Tools

| Tool | Ops |
|------|-----|
| `comfy_generate` | image, video, upscale, inpaint, edit |
| `comfy_workflows` | list, get, validate, register |
| `comfy_models` | list_installed, check_vram, health |
| `comfy_library` | recent, search, record |
| `comfy_agentic_assist` | Multi-step via MCP sampling |

## Links

- [Installation Guide](INSTALL.md)
- [Configuration](docs/CONFIGURATION.md) — env vars reference
- [Tool Reference](docs/TOOLS.md) — full parameter docs
- [Development](docs/DEVELOPMENT.md) — setup, testing, contributing
- [Troubleshooting](docs/TROUBLESHOOTING.md) — common issues
- [CHANGELOG](CHANGELOG.md)

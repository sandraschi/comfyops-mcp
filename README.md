# comfyops-mcp — Local Generative AI Engine

Wraps ComfyUI so you can generate images, video, and upscales from a prompt — without ever touching the node editor. Pick a curated workflow, type what you want, get a PNG or MP4.

**FastMCP 3.4+** | 5 portmanteau tools | 6 curated workflows | ComfyUI :11086 | Backend :11087 | Dashboard :11088

<p align="center">
  <img src="https://img.shields.io/badge/FastMCP-3.4+-7c5cfc?style=flat-square" alt="FastMCP">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/badge/status-MVP-orange?style=flat-square" alt="Status">
</p>

## Comfy for the Perplexed

**What's ComfyUI?** It's the engine room of local AI image generation. You connect boxes labelled "KSampler", "CLIP Text Encode", and "VAE Decode" with wires, like a Moog synthesizer made by someone who hates knobs. It's incredibly powerful and completely impenetrable.

**What's this?** comfyops-mcp is a butler for ComfyUI. You tell it what you want — "a cat surfing on a pizza slice" — and it picks the right boxes, wires them up, and hands you the result. No node editor, no patch cables, no "what's a CFG scale?"

**What can it do?**
- Turn text into images (FLUX.2, SDXL)
- Turn text or photos into short videos (Wan 2.2)
- Upscale old low-res images to 4K (ESRGAN)
- Inpaint: replace parts of an image ("make that car red")
- Browse and catalog workflows from the community
- Remember every generation with its seed so you can reproduce it later

**Who is it for?**
- **You, who just wants pictures** — prompt in, PNG out
- **You, who has an RTX 4090 gathering dust** — put it to work
- **You, who already uses ComfyUI** — now your AI assistant can drive it
- **You, who saw a cool AI image online and wants to make one**

> **If you already know ComfyUI:** comfyops registers curated workflows from `workflows/` as MCP tools. You can add your own with `comfy_workflows/register`. The workflows dir is yours — export from the node editor, drop in, done.

## Preview

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

See [docs/ONBOARDING.md](docs/ONBOARDING.md) for first-run (ComfyUI + models), and [INSTALL.md](INSTALL.md) for Claude Desktop config.

**Models from Civitai:** use [civitai-mcp](../civitai-mcp) to search/download into the ComfyUI models tree; this repo generates.

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

## Workflow Depot

comfyops ships with 6 curated workflows, but the community has thousands. Use `comfy_workflows/discover` to pull from community sources, or `comfy_workflows/register` to add your own exports from the ComfyUI node editor. The webapp has a full recipe browser with tags, metadata, and search.

## Tools

| Tool | Ops |
|------|-----|
| `comfy_generate` | image, video, upscale, inpaint, edit |
| `comfy_workflows` | list, get, validate, register, search, discover |
| `comfy_models` | list_installed, check_vram, health |
| `comfy_library` | recent, search, record |
| `comfy_agentic_assist` | Multi-step via MCP sampling |

## Community

- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI) — the project we wrap
- [ComfyUI Discord](https://discord.gg/comfyui) — 100k+ members, workflow sharing, troubleshooting
- [ComfyUI Workflows on Reddit](https://www.reddit.com/r/comfyui/) — daily shared workflows
- [CivitAI](https://civitai.com) — models, LoRAs, and workflow downloads
- [ComfyUI Registry](https://registry.comfy.org) — official workflow and node registry
- [OpenArt](https://openart.ai) — community workflows with parameter previews
- [ComfyUI Examples](https://comfyanonymous.github.io/ComfyUI_examples/) — official example gallery

## Links

- [Onboarding](docs/ONBOARDING.md) — ComfyUI, ports, civitai handoff
- [Installation Guide](INSTALL.md)
- [Configuration](docs/CONFIGURATION.md) — env vars reference
- [Tool Reference](docs/TOOLS.md) — full parameter docs
- [Development](docs/DEVELOPMENT.md) — setup, testing, contributing
- [Troubleshooting](docs/TROUBLESHOOTING.md) — common issues
- [CHANGELOG](CHANGELOG.md)
- Fleet start: `mcp-central-docs/starts/comfyops-mcp-start.bat`

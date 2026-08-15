# ComfyOps — Product Requirements Document

**Version**: 0.1.1 (2026-08-15)
**Repo**: `D:\Dev\repos\comfyops-mcp` | **GitHub**: https://github.com/sandraschi/comfyops-mcp
**Status**: MVP shipped — acceptance verified on FLUX.2 klein (seed-reproducible)

## Purpose

A local generative AI engine that wraps ComfyUI as a managed sidecar. Users pick a
curated workflow and describe what they want in natural language — the server handles
workflow JSON submission, GPU resource guarding, result polling, and history. No
ComfyUI node-editor knowledge required.

## Architecture

```
comfyops-mcp (FastMCP 3.4+, HTTP :11087 + stdio)
   |-- comfy_generate   - submit curated workflow, VRAM guard, poll, return files
   |-- comfy_workflows  - curated workflow depot (27 JSONs in workflows/)
   |-- comfy_models     - list_installed / download (HF, hash-verified) / check_vram / health
   |-- comfy_library    - SQLite generation history (gallery data)
   |-- comfy_agentic_assist - SEP-1577 sampling (multi-step goals)
   |
   |-- Starlette REST bridge (:11087) - /api/health, /api/models, /api/gallery*,
   |       /api/generate, /api/workflows, /api/prompt*, /api/nodes*
   |
   |--> ComfyUI sidecar (:11086, venv python, auto-spawned) --vram--> RTX 4090
   |
   '--> Vite + React + Tailwind webapp (:11088) - Dashboard, Generate, Gallery,
        Workflows, Models, Discover, Help, Settings
```

## Ports

| Port | Service |
|------|---------|
| 11086 | ComfyUI sidecar (API mode) |
| 11087 | Backend (FastAPI + FastMCP HTTP `/mcp` + REST `/api/*`) |
| 11088 | Frontend (Vite dev server) |

## Tools

| Tool | Ops | Covers |
|------|-----|--------|
| comfy_generate | image, video, upscale, inpaint, edit | Submit workflow, poll, return outputs |
| comfy_workflows | list, get, validate, register | Curated workflow depot |
| comfy_models | list_installed, download, check_vram, health | Local models + HF downloads + GPU status |
| comfy_library | recent, search, record | SQLite generation history |
| comfy_agentic_assist | — | Sampling-driven multi-step generation |

## Shipped Features (v0.1.1)

- Verified text-to-image: FLUX.2 klein 4B fp8 (~11.7GB total: klein unet 3.9GB +
  qwen_3_4b encoder 7.5GB + flux2-vae 0.3GB) — seed-reproducible, ~1-2 min per 1024²
- Verified text-to-image: SD 1.5 (sd15-t2i, checkpoints/sd_v1-5.safetensors)
- comfy_models download: streaming HF downloads, sha256 verify, subdir allowlist,
  Bearer auth for gated repos (COMFYOPS_HF_TOKEN)
- Gallery webapp: sorting, filters, batch delete/export (CSV/JSON), crossconnects
- ComfyUI lifecycle: auto-spawn with own venv, /free after runs (VRAM honesty),
  robust history polling
- 27 curated workflows (t2i, i2v, t2v, inpaint, edit, upscale, restore)
- VRAM guard before queueing (per-workflow estimates in _MODEL_VRAM_MAP)

## Known Gaps

- Video (i2v/t2v) and upscale workflows are curated but **not verified end-to-end**
  (Wan 2.1 t2v unet present; generation untested as of 0.1.1)
- comfy_agentic_assist requires a host that supports MCP sampling
- Auto-ingest (Immich/Plex) and Phase 2 (LoRA) from the original brief: not built
- `/mcp` streamable-HTTP transport 500s on tools/call without a session handshake
  (REST bridge + MCP stdio are the tested paths)

## Quick Start

```
D:\Dev\repos\mcp-central-docs\starts\comfyops-mcp-start.bat   # full stack
http://127.0.0.1:11088                                        # webapp
```

Requires: ComfyUI at `D:\ComfyUI` (v0.33+, its own venv with torch cu128), models
in `D:\ComfyUI\models\` (see docs/ONBOARDING.md), optional `COMFYOPS_HF_TOKEN` for
gated HF repos. `.env` at repo root is the single config source.

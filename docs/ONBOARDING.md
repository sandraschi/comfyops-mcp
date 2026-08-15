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

1. Install ComfyUI (typical: `D:\ComfyUI`) and confirm it boots. Keep it updated:
   `git -C D:\ComfyUI pull` + `D:\ComfyUI\.venv\Scripts\python.exe -m pip install -r requirements.txt`
   (0.33+; the venv needs a CUDA torch from the pytorch index, e.g. `torch 2.11+cu128`).
2. Get models. Two ways:
   - `comfy_models/download` (MCP tool): streams from Hugging Face with optional
     sha256 verification; set `COMFYOPS_HF_TOKEN` in `.env` for gated repos.
   - civitai-mcp (ports 11124/11125) for CivitAI downloads.
3. In this repo:

```powershell
cd D:\Dev\repos\comfyops-mcp
Copy-Item .env.example .env
# Edit: COMFYOPS_COMFYUI_DIR, COMFYOPS_MODELS_DIR (keep = ComfyUI's models tree), ports if needed
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

### Verified model set for text-to-image (~11.7 GB)

| File | Location | Source |
|------|----------|--------|
| `flux-2-klein-4b-fp8.safetensors` | `models/diffusion_models/` | `black-forest-labs/FLUX.2-klein-4b-fp8` |
| `qwen_3_4b.safetensors` | `models/text_encoders/` | `Comfy-Org/flux2-klein` (split_files/text_encoders/) |
| `flux2-vae.safetensors` | `models/vae/` | `Comfy-Org/flux2-dev` (split_files/vae/flux2-vae.safetensors) |

sha256s are recorded in `models_manifest.yaml`. Workflow: `flux2-klein-t2i`
(sd15-t2i works with `sd_v1-5.safetensors` in `models/checkpoints/`).

## Ports

| Port | Role |
|------|------|
| 11086 | ComfyUI sidecar |
| 11087 | FastMCP / REST backend |
| 11088 | Vite dashboard (`web_sota/`) |

## Pitfalls

- **ComfyUI offline** → dashboard shows red onboarding; generation tools fail until sidecar is up
- **Empty models dir** → workflows queue but fail; fill via comfy_models/download or civitai-mcp
- **Wrong models path** — ComfyUI only loads from its own `models/` tree; keep `COMFYOPS_MODELS_DIR` aligned
- **Stale VRAM guard** — ComfyUI keeps encoders resident after a run; comfyops calls
  POST /free after each generation, so consecutive jobs see honest free VRAM
- **Slow first run** — the qwen encoder loads into VRAM on first use; allow a minute
- **FLUX.1-klein is discontinued** — BFL's org now ships FLUX.2-klein; use `flux2-klein-t2i`

## Related docs

- [CONFIGURATION.md](CONFIGURATION.md) — env vars
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — common failures
- [TOOLS.md](TOOLS.md) — MCP portmanteau ops

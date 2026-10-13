# Handover Document for Claude (`comfyops-mcp`)

**Repository:** `comfyops-mcp`  
**Last Updated:** 2026-08-21  
**Status:** Operational (v0.1.3) · 31 Curated Workflows · Dual Hands-In/Hands-Off Modes · 100% Test Pass Rate  

---

## 1. System Architecture & Ports

| Component | Port / Scheme | Description |
|---|---|---|
| **ComfyUI Sidecar** | `http://127.0.0.1:11086` | Native ComfyUI web engine (`main.py`) |
| **FastMCP Backend** | `http://127.0.0.1:11087` | FastMCP 3.4+ portmanteau tool server |
| **SOTA Web Dashboard** | `http://127.0.0.1:11088` | Vite + React + Tailwind dashboard (`web_sota`) |

---

## 2. Recent Major Accomplishments (v0.1.3)

1. **Meituan LongCat-Video 13.6B DiT Workflows:**
   - **Curated Workflows:** Added [`workflows/longcat-t2v.json`](../workflows/longcat-t2v.json) (720p @ 30 FPS Text-to-Video) and [`workflows/longcat-extend.json`](../workflows/longcat-extend.json) (Video Continuation).
   - **VRAM Guard:** Registered 16.0 GB VRAM allocation in `_MODEL_VRAM_MAP` inside [`src/comfyops_mcp/tools/generate.py`](../src/comfyops_mcp/tools/generate.py).
   - **Models Manifest:** Added `longcat-video-13b` candidate entry in [`models_manifest.yaml`](../models_manifest.yaml).

2. **Dual Operating Modes (Hands-In & Hands-Off):**
   - Added `open_gui` operation to `comfy_workflows` to launch `http://127.0.0.1:11086` directly in the user's browser.
   - Preserves full manual canvas node placement and wiring capability alongside FastMCP automated prompt submission.

3. **2D Node Placement Optimization Algorithm (`api_to_ui`):**
   - Implemented `api_to_ui()` in [`src/comfyops_mcp/workflow_utils.py`](../src/comfyops_mcp/workflow_utils.py) using topological graph depth sorting.
   - Automatically calculates screen coordinates ($x = \text{depth} \times 380\text{px}$, $y = \text{row} \times 260\text{px}$) and link IDs to render raw headless API JSON graphs onto the visual canvas without overlapping nodes or crossed wires.

---

## 3. FastMCP Tool Surface (5 Portmanteau Tools)

1. `comfy_generate`: `image`, `video`, `upscale`, `inpaint`, `edit`.
2. `comfy_workflows`: `list`, `get`, `validate`, `register`, `search`, `discover`, `open_gui`.
3. `comfy_models`: `list_installed`, `download`, `check_vram`, `health`.
4. `comfy_library`: `recent`, `search`, `record`.
5. `comfy_agentic_assist`: SEP-1577 sampling assistance.

---

## 4. Verification Commands

```powershell
# Run comfyops-mcp test suite
uv run pytest tests/test_longcat_workflows.py tests/test_workflow_layout.py tests/test_generate.py -q
```

---

*Handover document prepared by Antigravity AI Orchestrator · 2026*

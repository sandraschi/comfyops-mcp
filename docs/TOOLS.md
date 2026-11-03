# Tool Reference

## comfy_generate

Generate images, video, upscales, and inpaints via curated ComfyUI workflows.

**Operations:** image, video, upscale, inpaint, edit

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | Generation type |
| `workflow_id` | str | Yes | Workflow ID from comfy_workflows/list |
| `prompt` | str | Yes | Text prompt |
| `seed` | int | No | Random seed (same seed = same output) |
| `size` | str | No | Image size as WxH (e.g. 1024x1024) |
| `negative_prompt` | str | No | Things to avoid |
| `image_input` | str | No | Base64 image for i2v/inpaint/edit |

**Returns:** `{success, prompt_id, outputs, seed, message}`

## comfy_workflows

Manage the curated workflow depot and discover community sources.

**Operations:** list, get, validate, register, search, discover

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | Operation |
| `workflow_id` | str | For get/validate/register | Workflow ID |
| `workflow_json` | str | For register | Full workflow JSON |
| `name` | str | No | Display name for register |
| `description` | str | No | Description for register |
| `query` | str | For search | Free-text search across names and descriptions |
| `tags` | str | For search/register | Comma-separated tags (e.g. "t2i,portrait,fast") |
| `source_url` | str | For register | Original source URL (CivitAI, OpenArt, etc.) |

**`discover`** returns a list of community sources:
- ComfyUI Examples (official)
- CivitAI (model + workflow marketplace)
- OpenArt (community workflows)
- ComfyUI Registry (official registry)
- r/comfyui (Reddit)
- ComfyUI Discord

## comfy_models

Manage local models, download from Hugging Face (hash-verified), and check GPU status.

**Operations:** list_installed, download, check_vram, health

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | Operation |
| `model_vram_gb` | float | For check_vram | Estimated VRAM requirement |

## comfy_comic

Panel-by-panel cartoon generation + strip assembly (Drive 2026-11-03 two-pass hybrid).

**Operations:** generate_panel, assemble_strip

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | generate_panel or assemble_strip |
| `prompt` | str | For generate_panel | Scene prompt, dialogue excluded (art pass) |
| `verbatim_dialogue` | str | No | Short exact text <=12 words for T5 orthography |
| `style_preset` | Literal | No | vintage_pulp, modern_graphic_novel, ligne_claire |
| `template` | str | No | flux_dev_panel (default) or flux_clean_balloon |
| `width` / `height` | int | No | Panel dims, default 1024x1024 |
| `seed` | int | No | Reproducibility seed |
| `panel_paths` | list[str] | For assemble_strip | Local PNGs left-to-right (4 for grid_2x2) |
| `layout` | Literal | No | horizontal_strip or grid_2x2 |
| `gutter_width` | int | No | Gutter px, default 24 |

**Returns generate_panel:** `{success, panel_path, markdown_preview, seed_used}`
**Returns assemble_strip:** `{success, strip_path, dimensions}`

Execution is WS-first (`/ws` streaming via `comfy_ws.py`) with `/history` poll fallback.
Artifacts persist to disk (`data/artifacts/comics/`) — zero base64 in JSON-RPC.

**Templates:** `flux_dev_panel` (scene + short text), `flux_clean_balloon`
(empty balloon space, dialogue composited deterministically in pass 2).

## comfy_library

Browse and record generations.

**Operations:** recent, search, record

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | Operation |
| `limit` | int | No | Max results (default 20) |
| `query` | str | For search | Search text across prompts |
| `prompt_id` | str | For record | Prompt ID to record |

## comfy_agentic_assist

Multi-step agentic generation planning via MCP sampling (SEP-1577).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal` | str | Yes | Natural language description of what to generate |

Requires a host with MCP sampling. Falls back to structured manual sequence when unavailable.

## Prefab Cards

| Card | Description |
|------|-------------|
| `show_comfyops_status_card` | Live ComfyUI health, VRAM, workflow count, model count |
| `show_generation_card` | Single generation result with prompt, seed, outputs |


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

Manage the curated workflow depot.

**Operations:** list, get, validate, register

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | Operation |
| `workflow_id` | str | For get/validate/register | Workflow ID |
| `workflow_json` | str | For register | Full workflow JSON |
| `name` | str | No | Display name for register |
| `description` | str | No | Description for register |

## comfy_models

Manage models and check GPU status.

**Operations:** list_installed, check_vram, health

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | Operation |
| `model_vram_gb` | float | For check_vram | Estimated VRAM requirement |

## comfy_library

Browse and record generations.

**Operations:** recent, search, record

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | Literal | Yes | Operation |
| `limit` | int | No | Max results (default 20) |
| `query` | str | For search | Search text |
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

"""comfy_generate portmanteau — image, video, upscale, inpaint, edit."""

import json
import logging
import random
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import Context, FastMCP

from comfyops_mcp import config as _cfg
from comfyops_mcp.comfyui_manager import (
    check_vram,
    ensure_comfyui_running,
    get_object_info,
    queue_prompt,
    wait_for_result,
)
from comfyops_mcp.manager_install import ensure_workflow_nodes
from comfyops_mcp.workflow_utils import normalize_for_prompt

logger = logging.getLogger(__name__)

_MODEL_VRAM_MAP = {
    "flux-klein-t2i": 6.0,
    "qwen-t2i-text": 8.0,
    "zimage-fast": 5.0,
    "sdxl-lora-t2i": 5.5,
    "wan22-t2v": 20.0,
    "wan22-i2v": 20.0,
    "ltx-fast-t2v": 8.0,
    "esrgan-upscale": 2.0,
    "supir-restore": 8.0,
    "flux-inpaint": 6.0,
}


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": False})
    async def comfy_generate(
        operation: Annotated[Literal["image", "video", "upscale", "inpaint", "edit"], "Generation type."],
        workflow_id: Annotated[str, "Workflow ID from comfy_workflows/list."],
        prompt: Annotated[str, "Text prompt for generation."],
        seed: Annotated[int | None, "Random seed for reproducibility. Omit for random."] = None,
        size: Annotated[str | None, "Image size as WxH (e.g. '1024x1024')."] = None,
        negative_prompt: Annotated[str | None, "Negative prompt."] = None,
        image_input: Annotated[str | None, "Base64 image for i2v/inpaint/edit."] = None,
        auto_install_nodes: Annotated[bool | None, "Install missing custom nodes via ComfyUI-Manager."] = None,
        ctx: Context = None,
    ) -> dict:
        """Generate image, video, or upscale via a curated ComfyUI workflow.

        ## RATIONALE
        Consolidated portmanteau: all generation modes share the same ComfyUI
        workflow submission and result polling pipeline. The operation
        discriminator selects the workflow type.

        ## Return Format
        {"success": bool, "prompt_id": str, "outputs": [...],
         "seed": int, "message": str}

        ## Examples
            comfy_generate(operation="image", workflow_id="flux-klein-t2i",
                           prompt="a cat surfing on a pizza slice", seed=42)
            comfy_generate(operation="upscale", workflow_id="esrgan-upscale",
                           prompt="", image_input="<base64>")
        """
        boot = await ensure_comfyui_running()
        if not boot.get("ok"):
            return {
                "success": False,
                "error": boot.get("error", "ComfyUI unavailable"),
                "error_type": "connection",
                "suggestions": boot.get("suggestions", ["Set COMFYOPS_COMFYUI_DIR."]),
            }

        model_vram = _MODEL_VRAM_MAP.get(workflow_id, 6.0)
        vram = await check_vram(model_vram)
        if not vram["ok"]:
            return {
                "success": False,
                "error": vram["error"],
                "error_type": "vram",
                "suggestions": ["Close other GPU apps (LM Studio, Ollama).", "Try a smaller model workflow."],
            }

        wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
        if not wf_path.exists():
            return {
                "success": False,
                "error": f"Workflow '{workflow_id}' not found.",
                "suggestions": ["Use comfy_workflows/list to see available workflows."],
            }

        workflow = json.loads(wf_path.read_text(encoding="utf-8"))
        seed_val = seed if seed is not None else random.randint(0, 2**32 - 1)
        workflow = _apply_params(workflow, prompt, seed_val, size, negative_prompt, image_input)

        info = await get_object_info()
        api_wf = normalize_for_prompt(workflow, info.get("object_info") if info.get("ok") else None)
        if info.get("ok"):
            node_check = await ensure_workflow_nodes(workflow, auto_install=auto_install_nodes)
            if not node_check.get("valid"):
                return {
                    "success": False,
                    "error": node_check.get("error") or node_check.get("message", "Missing nodes"),
                    "error_type": "missing_nodes",
                    "missing_types": node_check.get("still_missing") or node_check.get("missing_types", []),
                    "installed": node_check.get("installed", []),
                    "unmapped_types": node_check.get("unmapped_types", []),
                    "suggestions": [
                        "comfy_nodes/resolve — map class_types to Manager packages.",
                        "comfy_nodes/install — install by package name.",
                        "Add _meta.required_packs to workflow JSON.",
                    ],
                }
            if node_check.get("installed"):
                info = await get_object_info()
                api_wf = normalize_for_prompt(workflow, info.get("object_info") if info.get("ok") else None)

        result = await queue_prompt(api_wf)
        if not result["ok"]:
            return {"success": False, "error": result["error"], "error_type": "comfyui"}

        prompt_id = result["prompt_id"]
        generation = await wait_for_result(prompt_id, _cfg.GENERATION_TIMEOUT)

        if not generation["ok"]:
            return {"success": False, "error": generation["error"], "error_type": "generation", "prompt_id": prompt_id}

        return {
            "success": True,
            "prompt_id": prompt_id,
            "outputs": generation.get("outputs", []),
            "seed": seed_val,
            "message": f"Generated {len(generation.get('outputs', []))} file(s) with seed {seed_val}.",
        }


def _apply_params(workflow, prompt, seed, size, negative_prompt, image_input):
    wf = json.loads(json.dumps(workflow))
    clip_encountered = 0
    for node_id, node in wf.items():
        if node_id.startswith("_"):
            continue
        cls = node.get("class_type", "")
        inputs = node.get("inputs", {})
        if cls == "CLIPTextEncode":
            if "text" in inputs:
                clip_encountered += 1
                if clip_encountered == 1:
                    inputs["text"] = prompt
                elif negative_prompt:
                    inputs["text"] = negative_prompt
        elif cls in ("KSampler", "SamplerCustom"):
            if "seed" in inputs:
                inputs["seed"] = seed
        elif cls == "EmptyLatentImage" and size:
            parts = size.split("x")
            if len(parts) == 2:
                inputs["width"] = int(parts[0])
                inputs["height"] = int(parts[1])
        elif cls == "LoadImage" and image_input:
            inputs["image"] = image_input
    return wf

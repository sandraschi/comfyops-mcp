"""comfy_models portmanteau — list_installed, check_vram, health."""

import logging
from typing import Annotated, Literal

from fastmcp import FastMCP

from comfyops_mcp.comfyui_manager import check_health, check_vram, list_models

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": True})
    async def comfy_models(
        operation: Annotated[Literal["list_installed", "check_vram", "health"], "Operation to perform."],
        model_vram_gb: Annotated[float | None, "Estimated VRAM for check_vram."] = None,
    ) -> dict:
        """Manage local models and check GPU VRAM status.

        ## Return Format
        {"success": bool, "models": [...], "vram": {...}, "health": {...}}

        ## Examples
            comfy_models(operation="list_installed")
            comfy_models(operation="check_vram", model_vram_gb=6.0)
            comfy_models(operation="health")
        """
        if operation == "list_installed":
            models = await list_models()
            total_gb = sum(m["size_mb"] for m in models) / 1024
            return {
                "success": True,
                "models": models,
                "count": len(models),
                "total_size_gb": round(total_gb, 1),
                "message": f"{len(models)} model files ({total_gb:.1f} GB).",
            }

        if operation == "check_vram":
            req = model_vram_gb if model_vram_gb else 4.0
            result = await check_vram(req)
            if not result["ok"]:
                return {
                    "success": False,
                    "error": result.get("error", "VRAM check failed"),
                    "error_type": "vram",
                    "vram_free": result.get("vram_free", 0),
                    "required": result.get("required", req),
                }
            return {
                "success": True,
                "vram_free": result["vram_free"],
                "required": result["required"],
                "message": f"{result['vram_free']} GB VRAM free (need ~{result['required']} GB).",
            }

        if operation == "health":
            health = await check_health()
            if not health["ok"]:
                return {
                    "success": False,
                    "error": health["error"],
                    "error_type": "connection",
                    "suggestions": ["Start ComfyUI first.", "Check COMFYOPS_COMFYUI_PORT and HOST."],
                }
            devices = health.get("cuda_devices", [])
            vram_total = health.get("vram_total", 0) / (1024**3) if health.get("vram_total") else 0
            vram_free = health.get("vram_free", 0) / (1024**3) if health.get("vram_free") else 0
            return {
                "success": True,
                "comfyui_version": health.get("comfyui_version", "unknown"),
                "cuda_devices": len(devices),
                "vram_total_gb": round(vram_total, 1),
                "vram_free_gb": round(vram_free, 1),
                "message": (
                    f"ComfyUI {health.get('comfyui_version', '?')} — "
                    f"{round(vram_free, 1)}/{round(vram_total, 1)} GB VRAM."
                ),
            }

        return {"success": False, "error": f"Unknown operation: {operation}"}

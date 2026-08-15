"""comfy_models portmanteau — list_installed, download, check_vram, health."""

import hashlib
import logging
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP

from comfyops_mcp import config as _cfg
from comfyops_mcp.comfyui_manager import check_health, check_vram, list_models

logger = logging.getLogger(__name__)

# Allowlisted ComfyUI model subdirectories - models land where ComfyUI reads them.
_ALLOWED_SUBDIRS = {
    "checkpoints",
    "diffusion_models",
    "loras",
    "text_encoders",
    "vae",
    "upscale_models",
    "clip",
    "clip_vision",
    "controlnet",
    "embeddings",
}

_HF_BASE = "https://huggingface.co"


async def _download_file(url: str, dest: Path, sha256: str | None = None, headers: dict | None = None) -> dict:
    """Stream a file from a URL, optionally verifying sha256. Returns metadata."""
    import httpx

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    digest = hashlib.sha256()
    total = 0
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        async with client.stream("GET", url, headers=headers or {}) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
    if sha256 and digest.hexdigest().lower() != sha256.lower():
        tmp.unlink(missing_ok=True)
        return {
            "ok": False,
            "error": f"sha256 mismatch: expected {sha256}, got {digest.hexdigest()}",
            "error_type": "hash",
        }
    tmp.replace(dest)
    return {
        "ok": True,
        "path": str(dest),
        "size_bytes": total,
        "size_mb": round(total / (1024**2), 1),
        "sha256": digest.hexdigest(),
        "verified": bool(sha256),
    }


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": False})
    async def comfy_models(
        operation: Annotated[
            Literal["list_installed", "download", "check_vram", "health"],
            "Operation to perform.",
        ],
        model_vram_gb: Annotated[float | None, "Estimated VRAM for check_vram."] = None,
        hf_repo: Annotated[
            str | None, "Hugging Face repo id for download (e.g. 'black-forest-labs/FLUX.1-schnell')."
        ] = None,
        filename: Annotated[str | None, "File name within the repo for download."] = None,
        target: Annotated[
            str | None,
            "ComfyUI model subdir (checkpoints, diffusion_models, loras, text_encoders, vae, upscale_models).",
        ] = None,
        sha256: Annotated[str | None, "Expected sha256 of the file (verified when provided)."] = None,
    ) -> dict:
        """Manage local models, download from Hugging Face (hash-verified), and check GPU VRAM.

        ## Return Format
        {"success": bool, "models": [...], "download": {...}, "vram": {...}, "health": {...}}

        ## Examples
            comfy_models(operation="list_installed")
            comfy_models(operation="check_vram", model_vram_gb=6.0)
            comfy_models(operation="download", hf_repo="org/model", filename="m.safetensors",
                         target="diffusion_models", sha256="<hash>")
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

        if operation == "download":
            if not hf_repo or not filename or not target:
                return {
                    "success": False,
                    "error": "download requires hf_repo, filename, and target",
                    "allowed_targets": sorted(_ALLOWED_SUBDIRS),
                }
            subdir = target.strip().strip("/").lower()
            if subdir not in _ALLOWED_SUBDIRS:
                return {
                    "success": False,
                    "error": f"target '{subdir}' not allowed",
                    "error_type": "validation",
                    "allowed_targets": sorted(_ALLOWED_SUBDIRS),
                }
            dest = Path(_cfg.MODELS_DIR) / subdir / filename
            url = f"{_HF_BASE}/{hf_repo}/resolve/main/{filename}"
            headers = {}
            if _cfg.HF_TOKEN:
                headers["Authorization"] = f"Bearer {_cfg.HF_TOKEN}"
            try:
                dl = await _download_file(url, dest, sha256, headers)
            except Exception as exc:
                return {"success": False, "error": str(exc), "error_type": type(exc).__name__}
            if not dl.get("ok"):
                return {"success": False, **dl}
            return {
                "success": True,
                "operation": operation,
                "download": dl,
                "message": (
                    f"Downloaded {filename} ({dl['size_mb']} MB) to {dest} "
                    f"{'with sha256 verification' if dl['verified'] else '- UNVERIFIED (no sha256 provided)'}"
                ),
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

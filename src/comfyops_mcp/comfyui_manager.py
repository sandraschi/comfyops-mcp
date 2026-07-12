"""ComfyUI sidecar lifecycle management and API client."""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional

import httpx

from comfyops_mcp.config import (
    COMFYUI_API_URL,
    COMFYUI_DIR,
    COMFYUI_HOST,
    COMFYUI_PORT,
    COMFYUI_URL,
    GENERATION_TIMEOUT,
    MODELS_DIR,
    WORKFLOWS_DIR,
)

logger = logging.getLogger(__name__)

_client: Optional[httpx.AsyncClient] = None
_comfyui_proc: Optional[subprocess.Popen] = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=COMFYUI_URL, timeout=30)
    return _client


async def check_health() -> dict:
    """Check if ComfyUI is running and report system stats."""
    try:
        client = get_client()
        r = await client.get("/system_stats", timeout=5)
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
        stats = r.json()
        return {
            "ok": True,
            "comfyui_version": stats.get("system", {}).get("comfyui_version", "unknown"),
            "cuda_devices": stats.get("system", {}).get("devices", []),
            "vram_free": stats.get("system", {}).get("memory", {}).get("free", 0),
            "vram_total": stats.get("system", {}).get("memory", {}).get("total", 0),
        }
    except httpx.ConnectError as e:
        return {"ok": False, "error": f"ComfyUI not reachable at {COMFYUI_URL}: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def check_vram(model_vram_gb: float = 4.0) -> dict:
    """Check if sufficient VRAM is available for a job.

    Returns overridden with 'ok' flags. estimate_gb is a crude heuristic —
    actual consumption depends on the model and workflow.
    """
    health = await check_health()
    if not health["ok"]:
        return {"ok": False, "vram_free": 0, "required": model_vram_gb, "error": health.get("error")}

    vram_free_gb = health.get("vram_free", 0) / (1024 ** 3)
    if vram_free_gb < model_vram_gb:
        return {
            "ok": False,
            "vram_free": round(vram_free_gb, 1),
            "required": model_vram_gb,
            "error": f"Only {vram_free_gb:.1f} GB VRAM free, need ~{model_vram_gb:.1f} GB. "
                     f"Try closing other GPU apps.",
        }
    return {"ok": True, "vram_free": round(vram_free_gb, 1), "required": model_vram_gb}


async def queue_prompt(workflow_json: dict) -> dict:
    """Submit a workflow JSON to ComfyUI's /prompt endpoint.

    Returns prompt_id on success. The prompt_id can be used to poll
    /history/{prompt_id} for the result.
    """
    client = get_client()
    payload = {"prompt": workflow_json}
    r = await client.post("/prompt", json=payload, timeout=30)
    if r.status_code != 200:
        err = r.text
        try:
            err = r.json().get("error", r.text)
        except json.JSONDecodeError:
            pass
        return {"ok": False, "error": f"ComfyUI prompt error ({r.status_code}): {err}"}
    result = r.json()
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        return {"ok": False, "error": f"No prompt_id in response: {result}"}
    return {"ok": True, "prompt_id": prompt_id}


async def wait_for_result(prompt_id: str, timeout: int = GENERATION_TIMEOUT) -> dict:
    """Poll /history/{prompt_id} until the generation completes or errors.

    Returns output image/video filenames and the node execution tree.
    """
    client = get_client()
    start = time.time()
    while time.time() - start < timeout:
        await asyncio.sleep(1)
        r = await client.get(f"/history/{prompt_id}", timeout=10)
        if r.status_code == 200:
            history = r.json()
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                status = history[prompt_id].get("status", {})
                completed = status.get("completed", False)
                if completed or status.get("status_str") == "success":
                    return {"ok": True, "outputs": _gather_outputs(outputs), "prompt_id": prompt_id}
                error = status.get("messages", [])
                return {"ok": False, "error": f"Generation failed: {error}", "prompt_id": prompt_id}
    return {"ok": False, "error": f"Timeout after {timeout}s", "prompt_id": prompt_id}


def _gather_outputs(outputs: dict) -> list:
    """Extract image/video filenames from ComfyUI node outputs."""
    files = []
    for node_id, node_output in outputs.items():
        for key, data in node_output.items():
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        filename = item.get("filename")
                        if filename:
                            files.append({"filename": filename, "type": item.get("type", "output"),
                                          "subfolder": item.get("subfolder", "")})
    return files


async def list_models() -> list:
    """Scan the models directory for available checkpoint/LoRA/VAE files."""
    models_dir = Path(MODELS_DIR)
    if not models_dir.exists():
        return []
    result = []
    for ext in (".safetensors", ".ckpt", ".pt", ".pth", ".bin"):
        for f in models_dir.rglob(f"*{ext}"):
            size_mb = f.stat().st_size / (1024 * 1024) if f.exists() else 0
            rel = f.relative_to(models_dir)
            result.append({"name": f.stem, "path": str(rel), "size_mb": round(size_mb, 1)})
    return sorted(result, key=lambda x: x["name"])


def get_workflow_depot() -> list:
    """List curated workflow JSONs from the workflows directory."""
    wf_dir = Path(WORKFLOWS_DIR)
    if not wf_dir.exists():
        return []
    workflows = []
    for f in sorted(wf_dir.glob("*.json")):
        wf_id = f.stem
        workflow = json.loads(f.read_text(encoding="utf-8"))
        meta = workflow.get("_meta", {})
        sidecar = f.with_suffix(".md")
        docs = sidecar.read_text(encoding="utf-8") if sidecar.exists() else ""
        workflows.append({
            "id": wf_id,
            "name": meta.get("name", wf_id),
            "description": meta.get("description", ""),
            "model_type": meta.get("model_type", "image"),
            "params": meta.get("params", {}),
            "docs": docs[:500] if docs else "",
        })
    return workflows


def start_sidecar() -> Optional[subprocess.Popen]:
    """Launch ComfyUI as a managed subprocess.

    Returns the Popen handle, or None if comfyui main.py isn't found.
    """
    global _comfyui_proc
    comfyui_main = Path(COMFYUI_DIR) / "main.py"
    if not comfyui_main.exists():
        logger.warning("ComfyUI not found at %s", comfyui_main)
        return None
    if _comfyui_proc and _comfyui_proc.poll() is None:
        logger.info("ComfyUI already running")
        return _comfyui_proc
    proc = subprocess.Popen(
        [sys.executable, "-m", "main", "--listen", COMFYUI_HOST, "--port", str(COMFYUI_PORT)],
        cwd=COMFYUI_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    _comfyui_proc = proc
    logger.info("Started ComfyUI (PID %d) on %s:%s", proc.pid, COMFYUI_HOST, COMFYUI_PORT)
    return proc


def stop_sidecar():
    global _comfyui_proc
    if _comfyui_proc and _comfyui_proc.poll() is None:
        _comfyui_proc.terminate()
        try:
            _comfyui_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _comfyui_proc.kill()
        _comfyui_proc = None


async def shutdown():
    global _client
    if _client:
        await _client.aclose()
        _client = None

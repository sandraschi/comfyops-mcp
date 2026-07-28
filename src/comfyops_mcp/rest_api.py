"""REST bridge for comfyops webapp — mirrors MCP tool behavior."""

from __future__ import annotations

import json
import logging
import random
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse

from comfyops_mcp import config as _cfg
from comfyops_mcp.comfyui_manager import (
    check_health,
    check_vram,
    ensure_comfyui_running,
    get_object_info,
    get_workflow_depot,
    list_models,
    queue_prompt,
    wait_for_result,
)
from comfyops_mcp.manager_install import (
    ensure_workflow_nodes,
    fetch_manager_catalog,
    install_git_url,
    install_packages,
    manager_status,
)
from comfyops_mcp.tools.generate import _MODEL_VRAM_MAP, _apply_params
from comfyops_mcp.workflow_utils import normalize_for_prompt, parse_workflow_json, validate_node_types

logger = logging.getLogger(__name__)


def _library_db() -> Path:
    return Path(_cfg.DATA_DIR) / "library.sqlite3"


def _library_recent(limit: int = 20) -> list[dict]:
    dbp = _library_db()
    if not dbp.exists():
        return []
    with sqlite3.connect(str(dbp)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT prompt_id, workflow_id, prompt, seed, model, outputs, created_at "
            "FROM generations ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    items = []
    for r in rows:
        try:
            outputs = json.loads(r["outputs"] or "[]")
        except json.JSONDecodeError:
            outputs = []
        items.append(
            {
                "prompt_id": r["prompt_id"],
                "prompt": r["prompt"],
                "seed": r["seed"],
                "workflow_id": r["workflow_id"],
                "model": r["model"],
                "date": r["created_at"],
                "outputs": outputs,
            }
        )
    return items


def _library_record(
    *,
    prompt_id: str,
    workflow_id: str,
    prompt: str,
    seed: int,
    model: str,
    outputs: list,
) -> None:
    dbp = _library_db()
    dbp.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(dbp)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT UNIQUE, workflow_id TEXT, prompt TEXT,
                seed INTEGER, model TEXT, params TEXT, outputs TEXT,
                created_at TEXT
            )
        """)
        conn.execute(
            "INSERT OR IGNORE INTO generations "
            "(prompt_id, workflow_id, prompt, seed, model, params, outputs, created_at) "
            "VALUES (?, ?, ?, ?, ?, '{}', ?, ?)",
            (
                prompt_id,
                workflow_id,
                prompt,
                seed,
                model,
                json.dumps(outputs),
                datetime.now(UTC).isoformat(),
            ),
        )


async def api_comfyui_health(_request: Request) -> JSONResponse:
    health = await check_health()
    if not health.get("ok"):
        return JSONResponse(
            {
                "ok": False,
                "error": health.get("error"),
                "message": health.get("error"),
            }
        )
    vram_total = (health.get("vram_total", 0) or 0) / (1024**3)
    vram_free = (health.get("vram_free", 0) or 0) / (1024**3)
    devices = health.get("cuda_devices") or []
    return JSONResponse(
        {
            "ok": True,
            "comfyui_version": health.get("comfyui_version", "unknown"),
            "cuda_devices": len(devices),
            "vram_total_gb": round(vram_total, 1),
            "vram_free_gb": round(vram_free, 1),
            "message": (
                f"ComfyUI {health.get('comfyui_version', '?')} — {round(vram_free, 1)}/{round(vram_total, 1)} GB VRAM."
            ),
        }
    )


async def api_comfyui_ensure(request: Request) -> JSONResponse:
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    timeout = int(body.get("timeout_seconds", 120))
    result = await ensure_comfyui_running(timeout=timeout)
    return JSONResponse(result, status_code=200 if result.get("ok") else 503)


async def api_workflows_list(_request: Request) -> JSONResponse:
    depot = get_workflow_depot()
    return JSONResponse({"success": True, "workflows": depot, "message": f"{len(depot)} workflows."})


async def api_workflows_get(request: Request) -> JSONResponse:
    workflow_id = request.path_params["workflow_id"]
    wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
    if not wf_path.exists():
        return JSONResponse({"success": False, "error": f"Workflow '{workflow_id}' not found."}, status_code=404)
    workflow = json.loads(wf_path.read_text(encoding="utf-8"))
    meta = workflow.get("_meta", {})
    sidecar = wf_path.with_suffix(".md")
    docs = sidecar.read_text(encoding="utf-8") if sidecar.exists() else ""
    return JSONResponse(
        {
            "success": True,
            "workflow": {
                "id": workflow_id,
                "name": meta.get("name", workflow_id),
                "description": meta.get("description", ""),
                "model_type": meta.get("model_type", "image"),
                "params": meta.get("params", {}),
                "docs": docs,
                "node_count": len([k for k in workflow if not k.startswith("_")]),
            },
        }
    )


async def api_workflows_validate(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"success": False, "error": "Invalid JSON body."}, status_code=400)

    workflow_id = body.get("workflow_id")
    raw = body.get("workflow_json")
    if workflow_id and not raw:
        wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
        if not wf_path.exists():
            return JSONResponse({"success": False, "error": "workflow not found."}, status_code=404)
        workflow = json.loads(wf_path.read_text(encoding="utf-8"))
    elif raw:
        workflow = parse_workflow_json(raw)
    else:
        return JSONResponse({"success": False, "error": "workflow_id or workflow_json required."}, status_code=400)

    info = await get_object_info()
    if not info.get("ok"):
        api_wf = normalize_for_prompt(workflow)
        return JSONResponse(
            {
                "success": True,
                "valid": True,
                "node_count": len(api_wf),
                "comfyui_reachable": False,
                "message": f"{len(api_wf)} nodes (ComfyUI offline — custom node check skipped).",
            }
        )

    report = validate_node_types(workflow, info["object_info"])
    return JSONResponse({"success": True, "comfyui_reachable": True, **report})


async def api_models_list(_request: Request) -> JSONResponse:
    models = await list_models()
    total_gb = sum(m["size_mb"] for m in models) / 1024
    return JSONResponse(
        {
            "success": True,
            "models": models,
            "count": len(models),
            "total_size_gb": round(total_gb, 1),
            "message": f"{len(models)} model files ({total_gb:.1f} GB).",
        }
    )


async def api_vram(request: Request) -> JSONResponse:
    model_vram_gb = float(request.query_params.get("model_vram_gb", "4.0"))
    result = await check_vram(model_vram_gb)
    status = 200 if result.get("ok") else 503
    return JSONResponse(result, status_code=status)


async def api_generate(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"success": False, "error": "Invalid JSON."}, status_code=400)

    workflow_id = body.get("workflow_id", "")
    prompt = body.get("prompt", "")
    seed = body.get("seed")
    size = body.get("size")
    negative_prompt = body.get("negative_prompt")
    image_input = body.get("image_input")
    ensure = body.get("ensure_comfyui", True)
    auto_install_nodes = body.get("auto_install_nodes")

    if not workflow_id:
        return JSONResponse({"success": False, "error": "workflow_id required."}, status_code=400)

    if ensure:
        boot = await ensure_comfyui_running()
        if not boot.get("ok"):
            return JSONResponse(
                {
                    "success": False,
                    "error": boot.get("error", "ComfyUI not running"),
                    "error_type": "connection",
                },
                status_code=503,
            )

    model_vram = _MODEL_VRAM_MAP.get(workflow_id, 6.0)
    vram = await check_vram(model_vram)
    if not vram.get("ok"):
        return JSONResponse(
            {
                "success": False,
                "error": vram.get("error"),
                "error_type": "vram",
            },
            status_code=503,
        )

    wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
    if not wf_path.exists():
        return JSONResponse({"success": False, "error": f"Workflow '{workflow_id}' not found."}, status_code=404)

    workflow = json.loads(wf_path.read_text(encoding="utf-8"))
    seed_val = int(seed) if seed is not None else random.randint(0, 2**32 - 1)
    workflow = _apply_params(workflow, prompt, seed_val, size, negative_prompt, image_input)

    info = await get_object_info()
    api_wf = normalize_for_prompt(workflow, info.get("object_info") if info.get("ok") else None)

    if info.get("ok"):
        node_check = await ensure_workflow_nodes(workflow, auto_install=auto_install_nodes)
        if not node_check.get("valid"):
            return JSONResponse(
                {
                    "success": False,
                    "error": node_check.get("error") or node_check.get("message"),
                    "error_type": "missing_nodes",
                    "missing_types": node_check.get("still_missing") or node_check.get("missing_types", []),
                    "installed": node_check.get("installed", []),
                    "unmapped_types": node_check.get("unmapped_types", []),
                },
                status_code=422,
            )
        if node_check.get("installed"):
            info = await get_object_info()
            api_wf = normalize_for_prompt(workflow, info.get("object_info") if info.get("ok") else None)

    result = await queue_prompt(api_wf)
    if not result.get("ok"):
        return JSONResponse(
            {
                "success": False,
                "error": result.get("error"),
                "error_type": "comfyui",
            },
            status_code=502,
        )

    prompt_id = result["prompt_id"]
    generation = await wait_for_result(prompt_id, _cfg.GENERATION_TIMEOUT)
    if not generation.get("ok"):
        return JSONResponse(
            {
                "success": False,
                "error": generation.get("error"),
                "error_type": "generation",
                "prompt_id": prompt_id,
            },
            status_code=502,
        )

    outputs = generation.get("outputs", [])
    _library_record(
        prompt_id=prompt_id,
        workflow_id=workflow_id,
        prompt=prompt,
        seed=seed_val,
        model=workflow_id,
        outputs=outputs,
    )
    return JSONResponse(
        {
            "success": True,
            "prompt_id": prompt_id,
            "outputs": outputs,
            "seed": seed_val,
            "message": f"Generated {len(outputs)} file(s) with seed {seed_val}.",
        }
    )


async def api_gallery_recent(request: Request) -> JSONResponse:
    limit = int(request.query_params.get("limit", "20"))
    items = _library_recent(limit)
    return JSONResponse({"success": True, "items": items})


async def api_nodes_status(_request: Request) -> JSONResponse:
    return JSONResponse({"success": True, **manager_status()})


async def api_nodes_install(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"success": False, "error": "Invalid JSON."}, status_code=400)

    git_url = body.get("git_url")
    packages_raw = body.get("packages") or body.get("package") or ""
    names = (
        packages_raw
        if isinstance(packages_raw, list)
        else [p.strip() for p in str(packages_raw).split(",") if p.strip()]
    )

    if git_url:
        result = await install_git_url(git_url)
    elif names:
        cat = await fetch_manager_catalog()
        result = await install_packages(names, cat.get("packs") or {})
    else:
        return JSONResponse({"success": False, "error": "packages or git_url required."}, status_code=400)

    if not result.get("ok"):
        return JSONResponse({"success": False, **result}, status_code=502)

    from comfyops_mcp.manager_install import restart_comfyui_after_install

    restart = await restart_comfyui_after_install()
    return JSONResponse({"success": True, "install": result, "restart": restart})


async def api_nodes_ensure(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"success": False, "error": "Invalid JSON."}, status_code=400)

    workflow_id = body.get("workflow_id")
    raw = body.get("workflow_json")
    auto_install = body.get("auto_install_nodes")

    if workflow_id:
        wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
        if not wf_path.exists():
            return JSONResponse({"success": False, "error": "workflow not found."}, status_code=404)
        workflow = json.loads(wf_path.read_text(encoding="utf-8"))
    elif raw:
        workflow = parse_workflow_json(raw)
    else:
        return JSONResponse({"success": False, "error": "workflow_id or workflow_json required."}, status_code=400)

    result = await ensure_workflow_nodes(workflow, auto_install=auto_install)
    status = 200 if result.get("valid") else 422
    return JSONResponse({"success": result.get("ok", False), **result}, status_code=status)

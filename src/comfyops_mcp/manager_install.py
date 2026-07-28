"""ComfyUI-Manager integration — resolve and install missing custom nodes."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from comfyops_mcp import config as _cfg
from comfyops_mcp.comfyui_manager import (
    check_health,
    ensure_comfyui_running,
    get_client,
    get_object_info,
    start_sidecar,
    stop_sidecar,
)
from comfyops_mcp.workflow_utils import validate_node_types

logger = logging.getLogger(__name__)

_MANAGER_REPO = "https://github.com/Comfy-Org/ComfyUI-Manager.git"
_mappings_cache: dict[str, Any] = {"at": 0.0, "class_to_pack": {}, "packs": {}}
_CACHE_TTL = 300.0


def manager_dir() -> Path:
    return Path(_cfg.COMFYUI_DIR) / "custom_nodes" / "ComfyUI-Manager"


def cm_cli_path() -> Path:
    return manager_dir() / "cm-cli.py"


def comfy_python_exe() -> Path:
    if _cfg.COMFYUI_PYTHON:
        return Path(_cfg.COMFYUI_PYTHON)
    candidates = [
        Path(_cfg.COMFYUI_DIR) / ".venv" / "Scripts" / "python.exe",
        Path(_cfg.COMFYUI_DIR) / "venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[-1]


def manager_status() -> dict[str, Any]:
    md = manager_dir()
    cli = cm_cli_path()
    return {
        "manager_dir": str(md),
        "manager_installed": md.is_dir() and cli.is_file(),
        "cm_cli": str(cli),
        "comfyui_dir": _cfg.COMFYUI_DIR,
        "python_exe": str(comfy_python_exe()),
        "auto_install_enabled": _cfg.AUTO_INSTALL_NODES,
        "bootstrap_enabled": _cfg.MANAGER_BOOTSTRAP,
    }


async def bootstrap_manager() -> dict[str, Any]:
    """Clone ComfyUI-Manager into custom_nodes when missing."""
    if manager_status()["manager_installed"]:
        return {"ok": True, "message": "ComfyUI-Manager already present.", "bootstrapped": False}
    if not _cfg.MANAGER_BOOTSTRAP:
        return {
            "ok": False,
            "error": "ComfyUI-Manager not installed and COMFYOPS_MANAGER_BOOTSTRAP=0.",
            "suggestions": [
                f"git clone {_MANAGER_REPO} {manager_dir()}",
            ],
        }
    dest = manager_dir()
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            _MANAGER_REPO,
            str(dest),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return {
                "ok": False,
                "error": f"git clone failed: {stderr.decode('utf-8', errors='replace')[:300]}",
            }
        return {"ok": True, "bootstrapped": True, "message": f"Cloned ComfyUI-Manager to {dest}."}
    except FileNotFoundError:
        return {"ok": False, "error": "git not found on PATH."}


def _invert_mappings(raw: dict[str, Any]) -> dict[str, str]:
    """Map ComfyUI node class_type -> package name."""
    out: dict[str, str] = {}
    for package, nodes in raw.items():
        if not isinstance(nodes, list):
            continue
        for item in nodes:
            if isinstance(item, list) and item:
                out[str(item[0])] = package
            elif isinstance(item, str):
                out[item] = package
    return out


async def fetch_manager_catalog(force: bool = False) -> dict[str, Any]:
    """Fetch class→pack map and pack metadata from ComfyUI-Manager HTTP API."""
    now = time.time()
    if not force and now - _mappings_cache["at"] < _CACHE_TTL and _mappings_cache["class_to_pack"]:
        return {"ok": True, **_mappings_cache}

    health = await check_health()
    if not health.get("ok"):
        return {"ok": False, "error": health.get("error", "ComfyUI offline")}

    client = get_client()
    try:
        map_resp = await client.get("/customnode/getmappings", params={"mode": "remote"}, timeout=60)
        list_resp = await client.get("/customnode/getlist", params={"mode": "remote"}, timeout=60)
    except httpx.HTTPError as exc:
        return {"ok": False, "error": str(exc)}

    if map_resp.status_code != 200:
        return {"ok": False, "error": f"getmappings HTTP {map_resp.status_code}"}
    if list_resp.status_code != 200:
        return {"ok": False, "error": f"getlist HTTP {list_resp.status_code}"}

    mappings_raw = map_resp.json()
    list_raw = list_resp.json()
    packs = list_raw.get("node_packs") or list_raw
    if isinstance(packs, dict) and "node_packs" in packs:
        packs = packs["node_packs"]

    class_to_pack = _invert_mappings(mappings_raw if isinstance(mappings_raw, dict) else {})
    _mappings_cache.update(
        {
            "at": now,
            "class_to_pack": class_to_pack,
            "packs": packs if isinstance(packs, dict) else {},
        }
    )
    return {"ok": True, "class_to_pack": class_to_pack, "packs": _mappings_cache["packs"]}


def packs_from_workflow_meta(workflow: dict[str, Any]) -> list[str]:
    meta = workflow.get("_meta") or {}
    packs: list[str] = []
    for key in ("required_packs", "node_packs", "custom_nodes"):
        val = meta.get(key)
        if isinstance(val, list):
            packs.extend(str(x) for x in val if x)
        elif isinstance(val, str) and val.strip():
            packs.extend(p.strip() for p in val.split(","))
    for node in meta.get("nodes") or []:
        if isinstance(node, dict) and node.get("name"):
            packs.append(str(node["name"]))
    return sorted(set(packs))


def resolve_packages_for_missing(
    missing_types: list[str],
    *,
    class_to_pack: dict[str, str],
    workflow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve missing class_types to ComfyUI-Manager package names."""
    packs: list[str] = []
    mapped: dict[str, str] = {}
    unmapped: list[str] = []

    if workflow:
        packs.extend(packs_from_workflow_meta(workflow))

    for ct in missing_types:
        pack = class_to_pack.get(ct)
        if pack:
            mapped[ct] = pack
            packs.append(pack)
        else:
            unmapped.append(ct)

    unique_packs = sorted(set(packs))
    return {
        "packages": unique_packs,
        "mapped": mapped,
        "unmapped_types": sorted(set(unmapped)),
    }


async def _install_via_cli(packages: list[str]) -> dict[str, Any]:
    boot = await bootstrap_manager()
    if not boot.get("ok") and not manager_status()["manager_installed"]:
        return boot

    cli = cm_cli_path()
    if not cli.is_file():
        return {"ok": False, "error": f"cm-cli not found at {cli}"}

    python = str(comfy_python_exe())
    env = os.environ.copy()
    env["COMFYUI_PATH"] = _cfg.COMFYUI_DIR

    cmd = [python, str(cli), "install", *packages, "--mode", "remote"]
    logger.info("ComfyUI-Manager CLI: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=_cfg.COMFYUI_DIR,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    out = stdout.decode("utf-8", errors="replace")
    err = stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": f"cm-cli exit {proc.returncode}",
            "stdout": out[-2000:],
            "stderr": err[-2000:],
            "packages": packages,
        }
    return {"ok": True, "method": "cm-cli", "packages": packages, "stdout": out[-2000:]}


async def _install_via_rest(packages: list[str], pack_meta: dict[str, Any]) -> dict[str, Any]:
    client = get_client()
    queued: list[str] = []
    for name in packages:
        meta = pack_meta.get(name) or {"name": name, "title": name}
        if "files" not in meta:
            meta = {**meta, "name": name}
        r = await client.post("/manager/queue/install", json=meta, timeout=30)
        if r.status_code not in (200, 201):
            return {"ok": False, "error": f"queue/install {name}: HTTP {r.status_code}", "detail": r.text[:300]}
        queued.append(name)

    start = await client.post("/manager/queue/start", timeout=30)
    if start.status_code not in (200, 201):
        return {"ok": False, "error": f"queue/start HTTP {start.status_code}"}

    deadline = time.time() + _cfg.MANAGER_INSTALL_TIMEOUT
    while time.time() < deadline:
        await asyncio.sleep(2)
        st = await client.get("/manager/queue/status", timeout=15)
        if st.status_code != 200:
            continue
        status = st.json()
        if not status.get("is_processing") and status.get("done_count", 0) >= status.get("total_count", 0):
            return {"ok": True, "method": "rest-queue", "packages": queued, "queue_status": status}
    return {"ok": False, "error": "Manager install queue timeout", "packages": queued}


async def install_packages(packages: list[str], pack_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Install custom node packs by catalog name."""
    if not packages:
        return {"ok": True, "installed": [], "message": "nothing to install"}

    cli_result = await _install_via_cli(packages)
    if cli_result.get("ok"):
        return cli_result

    health = await check_health()
    if health.get("ok"):
        rest = await _install_via_rest(packages, pack_meta or {})
        if rest.get("ok"):
            return rest
        return {
            "ok": False,
            "error": rest.get("error") or cli_result.get("error"),
            "cli": cli_result,
            "rest": rest,
        }
    return cli_result


async def install_git_url(url: str) -> dict[str, Any]:
    """Install a custom node from a git URL via Manager REST API."""
    boot = await ensure_comfyui_running(timeout=60)
    if not boot.get("ok"):
        return {"ok": False, "error": boot.get("error", "ComfyUI unavailable")}
    client = get_client()
    try:
        r = await client.post(
            "/customnode/install/git_url",
            content=url,
            headers={"Content-Type": "text/plain"},
            timeout=600,
        )
    except httpx.HTTPError as exc:
        return {"ok": False, "error": str(exc)}
    if r.status_code == 200:
        return {"ok": True, "method": "git_url", "url": url, "detail": r.text[:500]}
    return {"ok": False, "error": f"HTTP {r.status_code}", "detail": r.text[:500]}


async def restart_comfyui_after_install() -> dict[str, Any]:
    """Restart sidecar so newly installed custom nodes load."""
    stop_sidecar()
    await asyncio.sleep(1)
    proc = start_sidecar()
    if proc is None:
        return {"ok": False, "error": "Could not restart ComfyUI sidecar."}
    return await ensure_comfyui_running(timeout=_cfg.MANAGER_INSTALL_TIMEOUT)


async def ensure_workflow_nodes(
    workflow: dict[str, Any],
    *,
    auto_install: bool | None = None,
) -> dict[str, Any]:
    """Validate workflow nodes; optionally install missing packs via ComfyUI-Manager."""
    do_install = _cfg.AUTO_INSTALL_NODES if auto_install is None else auto_install

    boot = await ensure_comfyui_running(timeout=120)
    if not boot.get("ok"):
        return {"ok": False, "error": boot.get("error"), "stage": "boot"}

    info = await get_object_info()
    if not info.get("ok"):
        return {"ok": False, "error": info.get("error"), "stage": "object_info"}

    check = validate_node_types(workflow, info["object_info"])
    if check["valid"]:
        return {"ok": True, "valid": True, "node_count": check["node_count"], "installed": []}

    missing = check["missing_types"]
    if not do_install:
        return {
            "ok": False,
            "valid": False,
            "missing_types": missing,
            "error": check["message"],
            "stage": "validate",
        }

    catalog = await fetch_manager_catalog()
    class_to_pack = catalog.get("class_to_pack") or {}
    pack_meta = catalog.get("packs") or {}
    if not class_to_pack and not packs_from_workflow_meta(workflow):
        return {
            "ok": False,
            "valid": False,
            "missing_types": missing,
            "error": "Cannot resolve packages — ComfyUI-Manager catalog unavailable.",
            "suggestions": [
                "Install ComfyUI-Manager in custom_nodes.",
                "Set workflow _meta.required_packs with package names.",
            ],
        }

    resolved = resolve_packages_for_missing(missing, class_to_pack=class_to_pack, workflow=workflow)
    if resolved["unmapped_types"] and not resolved["packages"]:
        return {
            "ok": False,
            "valid": False,
            "missing_types": missing,
            "unmapped_types": resolved["unmapped_types"],
            "error": f"No Manager package mapping for: {', '.join(resolved['unmapped_types'])}",
        }

    install_result = await install_packages(resolved["packages"], pack_meta)
    if not install_result.get("ok"):
        return {
            "ok": False,
            "valid": False,
            "missing_types": missing,
            "packages_attempted": resolved["packages"],
            "install_error": install_result.get("error"),
            "install_detail": install_result,
        }

    restart = await restart_comfyui_after_install()
    if not restart.get("ok"):
        return {
            "ok": False,
            "valid": False,
            "installed": resolved["packages"],
            "error": restart.get("error"),
            "stage": "restart",
        }

    info2 = await get_object_info()
    if not info2.get("ok"):
        return {"ok": False, "error": info2.get("error"), "stage": "object_info_after"}

    check2 = validate_node_types(workflow, info2["object_info"])
    return {
        "ok": check2["valid"],
        "valid": check2["valid"],
        "installed": resolved["packages"],
        "mapped": resolved["mapped"],
        "still_missing": check2.get("missing_types", []),
        "unmapped_types": resolved["unmapped_types"],
        "message": check2["message"],
        "install_method": install_result.get("method"),
    }


async def ensure_workflow_nodes_by_id(
    workflow_id: str,
    *,
    auto_install: bool | None = None,
) -> dict[str, Any]:
    wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
    if not wf_path.exists():
        return {"ok": False, "error": f"Workflow '{workflow_id}' not found."}
    workflow = json.loads(wf_path.read_text(encoding="utf-8"))
    result = await ensure_workflow_nodes(workflow, auto_install=auto_install)
    result["workflow_id"] = workflow_id
    return result

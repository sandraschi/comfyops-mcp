"""comfy_nodes portmanteau — Manager status, resolve, install, ensure."""

import json
import logging
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP

from comfyops_mcp import config as _cfg
from comfyops_mcp.manager_install import (
    ensure_workflow_nodes,
    ensure_workflow_nodes_by_id,
    fetch_manager_catalog,
    install_git_url,
    install_packages,
    manager_status,
    resolve_packages_for_missing,
)
from comfyops_mcp.workflow_utils import parse_workflow_json

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": False})
    async def comfy_nodes(
        operation: Annotated[
            Literal["status", "mappings", "resolve", "install", "install_git", "ensure"],
            "Operation to perform.",
        ],
        workflow_id: Annotated[str | None, "Workflow ID for ensure/resolve."] = None,
        workflow_json: Annotated[str | None, "Raw workflow JSON for ensure/resolve."] = None,
        missing_types: Annotated[str | None, "Comma-separated class_types for resolve."] = None,
        packages: Annotated[str | None, "Comma-separated Manager package names for install."] = None,
        git_url: Annotated[str | None, "Git repo URL for install_git."] = None,
        auto_install: Annotated[bool | None, "Override COMFYOPS_AUTO_INSTALL_NODES."] = None,
    ) -> dict:
        """Install and resolve ComfyUI custom nodes via ComfyUI-Manager.

        Maps missing node class_types → Manager packages (registry/GitHub catalog),
        installs via cm-cli or Manager REST queue, restarts ComfyUI, re-validates.

        ## Return Format
        {"success": bool, "packages": [...], "mapped": {...}, "message": str}

        ## Examples
            comfy_nodes(operation="status")
            comfy_nodes(operation="ensure", workflow_id="my-complex-wf")
            comfy_nodes(operation="install", packages="ComfyUI-Impact-Pack,ComfyUI-VideoHelperSuite")
            comfy_nodes(operation="resolve", missing_types="ImpactInt,VHS_LoadVideo")
        """
        if operation == "status":
            st = manager_status()
            return {"success": True, **st, "message": "ComfyUI-Manager status."}

        if operation == "mappings":
            cat = await fetch_manager_catalog()
            if not cat.get("ok"):
                return {"success": False, "error": cat.get("error")}
            sample = dict(list((cat.get("class_to_pack") or {}).items())[:40])
            return {
                "success": True,
                "mapping_count": len(cat.get("class_to_pack") or {}),
                "pack_count": len(cat.get("packs") or {}),
                "sample_mappings": sample,
                "message": f"{len(cat.get('class_to_pack') or {})} class→package mappings loaded.",
            }

        if operation == "resolve":
            types = [t.strip() for t in (missing_types or "").split(",") if t.strip()]
            workflow = None
            if workflow_json:
                workflow = parse_workflow_json(workflow_json)
            elif workflow_id:
                wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
                if wf_path.exists():
                    workflow = json.loads(wf_path.read_text(encoding="utf-8"))
            cat = await fetch_manager_catalog(force=True)
            resolved = resolve_packages_for_missing(
                types,
                class_to_pack=cat.get("class_to_pack") or {},
                workflow=workflow,
            )
            return {"success": True, **resolved, "message": f"Resolved {len(resolved['packages'])} packages."}

        if operation == "install":
            names = [p.strip() for p in (packages or "").split(",") if p.strip()]
            if not names:
                return {"success": False, "error": "packages required (comma-separated Manager names)."}
            cat = await fetch_manager_catalog()
            result = await install_packages(names, cat.get("packs") or {})
            if not result.get("ok"):
                return {"success": False, **result}
            from comfyops_mcp.manager_install import restart_comfyui_after_install

            restart = await restart_comfyui_after_install()
            return {
                "success": True,
                "installed": names,
                "restart": restart,
                "message": f"Installed {len(names)} package(s). ComfyUI restarted.",
            }

        if operation == "install_git":
            if not git_url:
                return {"success": False, "error": "git_url required."}
            result = await install_git_url(git_url)
            if not result.get("ok"):
                return {"success": False, **result}
            from comfyops_mcp.manager_install import restart_comfyui_after_install

            restart = await restart_comfyui_after_install()
            return {"success": True, "url": git_url, "restart": restart, "message": "Git install complete."}

        if operation == "ensure":
            if workflow_id:
                result = await ensure_workflow_nodes_by_id(workflow_id, auto_install=auto_install)
            elif workflow_json:
                result = await ensure_workflow_nodes(parse_workflow_json(workflow_json), auto_install=auto_install)
            else:
                return {"success": False, "error": "workflow_id or workflow_json required."}
            return {"success": result.get("ok", False), **result}

        return {"success": False, "error": f"Unknown operation: {operation}"}

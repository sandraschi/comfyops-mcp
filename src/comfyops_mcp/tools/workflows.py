"""comfy_workflows portmanteau — list, get, validate, register."""

import json
import logging
from pathlib import Path
from typing import Annotated, Literal, Optional

from fastmcp import FastMCP

from comfyops_mcp.comfyui_manager import get_workflow_depot
from comfyops_mcp.config import WORKFLOWS_DIR

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": True})
    async def comfy_workflows(
        operation: Annotated[Literal["list", "get", "validate", "register"],
                             "Operation to perform."],
        workflow_id: Annotated[Optional[str], "Workflow ID for get/validate/register."] = None,
        workflow_json: Annotated[Optional[str], "JSON string for register."] = None,
        name: Annotated[Optional[str], "Display name for register."] = None,
        description: Annotated[Optional[str], "Description for register."] = None,
    ) -> dict:
        """Manage curated ComfyUI workflow definitions.

        ## Return Format
        {"success": bool, "workflows": [...], "workflow": {...}, "error": str}

        ## Examples
            comfy_workflows(operation="list")
            comfy_workflows(operation="get", workflow_id="flux-klein-t2i")
            comfy_workflows(operation="register", workflow_id="my-wf",
                            workflow_json='{"3":{"class_type":"KSampler",...}}')
        """
        depot = get_workflow_depot()

        if operation == "list":
            return {"success": True, "workflows": depot,
                    "message": f"{len(depot)} workflows available."}

        if operation == "get":
            if not workflow_id:
                return {"success": False, "error": "workflow_id required."}
            wf_path = Path(WORKFLOWS_DIR) / f"{workflow_id}.json"
            if not wf_path.exists():
                return {"success": False,
                        "error": f"Workflow '{workflow_id}' not found.",
                        "suggestions": [f"Available: {', '.join(w['id'] for w in depot[:10])}"]}
            workflow = json.loads(wf_path.read_text(encoding="utf-8"))
            meta = workflow.get("_meta", {})
            sidecar = wf_path.with_suffix(".md")
            docs = sidecar.read_text(encoding="utf-8") if sidecar.exists() else ""
            return {"success": True, "workflow": {
                "id": workflow_id, "name": meta.get("name", workflow_id),
                "description": meta.get("description", ""),
                "model_type": meta.get("model_type", "image"),
                "params": meta.get("params", {}), "docs": docs,
                "node_count": len([k for k in workflow if not k.startswith("_")]),
            }}

        if operation == "validate":
            if not workflow_id:
                return {"success": False, "error": "workflow_id required."}
            wf_path = Path(WORKFLOWS_DIR) / f"{workflow_id}.json"
            if not wf_path.exists():
                return {"success": False, "error": f"Workflow '{workflow_id}' not found."}
            try:
                data = json.loads(wf_path.read_text(encoding="utf-8"))
                nodes = [k for k in data if not k.startswith("_")]
                return {"success": True, "valid": True, "node_count": len(nodes),
                        "message": f"Workflow '{workflow_id}' has {len(nodes)} nodes."}
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON: {e}"}

        if operation == "register":
            if not workflow_id or not workflow_json:
                return {"success": False, "error": "workflow_id and workflow_json required."}
            try:
                data = json.loads(workflow_json)
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON: {e}"}
            meta = data.setdefault("_meta", {})
            if name:
                meta["name"] = name
            if description:
                meta["description"] = description
            wf_path = Path(WORKFLOWS_DIR) / f"{workflow_id}.json"
            wf_path.parent.mkdir(parents=True, exist_ok=True)
            wf_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return {"success": True, "message": f"Registered workflow '{workflow_id}'.",
                    "workflow_id": workflow_id,
                    "node_count": len([k for k in data if not k.startswith("_")])}

        return {"success": False, "error": f"Unknown operation: {operation}"}

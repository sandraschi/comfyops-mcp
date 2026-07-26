"""comfy_workflows portmanteau — list, get, validate, register, search, discover."""

import json
import logging
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP

from comfyops_mcp import config as _cfg
from comfyops_mcp.comfyui_manager import get_workflow_depot

logger = logging.getLogger(__name__)

_COMMUNITY_SOURCES = [
    {"name": "ComfyUI Examples", "url": "https://comfyanonymous.github.io/ComfyUI_examples/",
     "type": "official"},
    {"name": "CivitAI", "url": "https://civitai.com", "type": "marketplace"},
    {"name": "OpenArt", "url": "https://openart.ai/workflows", "type": "community"},
    {"name": "ComfyUI Registry", "url": "https://registry.comfy.org", "type": "registry"},
    {"name": "r/comfyui", "url": "https://www.reddit.com/r/comfyui/", "type": "community"},
    {"name": "ComfyUI Discord", "url": "https://discord.gg/comfyui", "type": "community"},
]


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": True})
    async def comfy_workflows(
        operation: Annotated[Literal["list", "get", "validate", "register", "search", "discover"],
                             "Operation to perform."],
        workflow_id: Annotated[str | None, "Workflow ID for get/validate/register."] = None,
        workflow_json: Annotated[str | None, "JSON string for register."] = None,
        name: Annotated[str | None, "Display name for register."] = None,
        description: Annotated[str | None, "Description for register."] = None,
        query: Annotated[str | None, "Search text for search operation."] = None,
        tags: Annotated[str | None, "Comma-separated tags for search/register."] = None,
        source_url: Annotated[str | None, "Original source URL for register."] = None,
    ) -> dict:
        """Manage curated ComfyUI workflow definitions.

        ## Return Format
        {"success": bool, "workflows": [...], "workflow": {...}, "sources": [...], "message": str}

        ## Examples
            comfy_workflows(operation="list")
            comfy_workflows(operation="search", query="flux", tags="video")
            comfy_workflows(operation="discover")
            comfy_workflows(operation="register", workflow_id="my-wf",
                            workflow_json='{"3":{"class_type":"KSampler",...}}',
                            tags="t2i,portrait", source_url="https://civitai.com/...")
        """
        if operation == "discover":
            return {"success": True, "sources": _COMMUNITY_SOURCES,
                    "message": f"{len(_COMMUNITY_SOURCES)} community sources for finding workflows. "
                               "Use comfy_workflows/register to add any you find."}

        if operation == "list":
            depot = get_workflow_depot()
            return {"success": True, "workflows": depot,
                    "message": f"{len(depot)} workflows in local depot."}

        if operation == "search":
            depot = get_workflow_depot()
            query_lower = (query or "").lower()
            tag_list = [t.strip().lower() for t in (tags or "").split(",") if t.strip()]
            results = []
            for wf in depot:
                name_match = query_lower in wf["name"].lower()
                desc_match = query_lower in wf["description"].lower()
                id_match = query_lower in wf["id"].lower()
                wf_tags = [t.strip().lower() for t in wf.get("params", {}).get("tags", "").split(",")]
                if not query_lower:
                    name_match = desc_match = id_match = True
                tag_match = any(t in wf_tags for t in tag_list) if tag_list else True
                if (name_match or desc_match or id_match) and tag_match:
                    results.append(wf)
            return {"success": True, "workflows": results,
                    "message": f"Found {len(results)} workflows matching '{query or tags}'."}

        if operation == "get":
            if not workflow_id:
                return {"success": False, "error": "workflow_id required."}
            wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
            if not wf_path.exists():
                available = [w["id"] for w in get_workflow_depot()]
                return {"success": False,
                        "error": f"Workflow '{workflow_id}' not found in local depot.",
                        "suggestions": [
                            f"Available locally: {', '.join(available[:10])}",
                            "Try comfy_workflows/discover to find more from the community.",
                        ]}
            workflow = json.loads(wf_path.read_text(encoding="utf-8"))
            meta = workflow.get("_meta", {})
            sidecar = wf_path.with_suffix(".md")
            docs = sidecar.read_text(encoding="utf-8") if sidecar.exists() else ""
            return {"success": True, "workflow": {
                "id": workflow_id, "name": meta.get("name", workflow_id),
                "description": meta.get("description", ""),
                "model_type": meta.get("model_type", "image"),
                "params": meta.get("params", {}),
                "tags": meta.get("tags", ""),
                "source_url": meta.get("source_url", ""),
                "docs": docs,
                "node_count": len([k for k in workflow if not k.startswith("_")]),
            }}

        if operation == "validate":
            if not workflow_id:
                return {"success": False, "error": "workflow_id required."}
            wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
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
            if tags:
                meta["tags"] = tags
            if source_url:
                meta["source_url"] = source_url
            wf_path = Path(_cfg.WORKFLOWS_DIR) / f"{workflow_id}.json"
            wf_path.parent.mkdir(parents=True, exist_ok=True)
            wf_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return {"success": True, "message": f"Registered workflow '{workflow_id}' in local depot.",
                    "workflow_id": workflow_id,
                    "node_count": len([k for k in data if not k.startswith("_")]),
                    "suggestions": ["Run comfy_workflows/search to find it in the depot.",
                                    "Add a sidecar .md file at workflows/{id}.md for human docs."]}

        return {"success": False, "error": f"Unknown operation: {operation}"}

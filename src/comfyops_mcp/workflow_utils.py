"""Normalize ComfyUI workflow JSON for API submission and validate node types."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def is_ui_format(workflow: dict[str, Any]) -> bool:
    return isinstance(workflow.get("nodes"), list)


def is_api_format(workflow: dict[str, Any]) -> bool:
    if is_ui_format(workflow):
        return False
    for key, val in workflow.items():
        if key.startswith("_"):
            continue
        if isinstance(val, dict) and "class_type" in val:
            return True
    return False


def strip_meta(workflow: dict[str, Any]) -> dict[str, Any]:
    """Remove _meta and other non-node keys before POST /prompt."""
    return {k: v for k, v in workflow.items() if not k.startswith("_")}


def ui_to_api(workflow: dict[str, Any], object_info: dict[str, Any] | None = None) -> dict[str, Any]:
    """Convert ComfyUI canvas (UI) export to API prompt format.

    Civitai/OpenArt exports are usually UI format. ComfyUI /prompt expects API format.
    Widget mapping uses object_info input order when provided; otherwise skips widgets
    (linked inputs still convert).
    """
    if not is_ui_format(workflow):
        return strip_meta(workflow)

    nodes = workflow.get("nodes") or []
    links = workflow.get("links") or []

    # links: [id, origin_id, origin_slot, target_id, target_slot, type]
    link_by_target: dict[tuple[int, int], tuple[str, int]] = {}
    for link in links:
        if not isinstance(link, (list, tuple)) or len(link) < 5:
            continue
        origin_id, origin_slot, target_id, target_slot = link[1], link[2], link[3], link[4]
        link_by_target[(int(target_id), int(target_slot))] = (str(origin_id), int(origin_slot))

    api: dict[str, Any] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        nid = str(node.get("id"))
        class_type = node.get("type") or node.get("class_type")
        if not nid or not class_type:
            continue

        inputs: dict[str, Any] = {}
        node_inputs = node.get("inputs") or []
        for slot_idx, inp in enumerate(node_inputs):
            if not isinstance(inp, dict):
                continue
            name = inp.get("name")
            if not name:
                continue
            key = (int(node["id"]), slot_idx)
            if key in link_by_target:
                inputs[name] = list(link_by_target[key])

        widgets = node.get("widgets_values") or []
        if widgets and object_info and class_type in object_info:
            spec = object_info[class_type].get("input", {})
            required = spec.get("required") or {}
            optional = spec.get("optional") or {}
            [
                name
                for name, meta in {**required, **optional}.items()
                if isinstance(meta, list)
                and meta
                and meta[0] not in ("INT", "FLOAT", "STRING", "BOOLEAN")
                and name not in inputs
            ]
            # Fallback: non-linked scalar inputs in definition order
            scalar_names = []
            for name, meta in {**required, **optional}.items():
                if name in inputs:
                    continue
                if isinstance(meta, list) and meta:
                    kind = meta[0]
                    if kind in ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"):
                        scalar_names.append(name)
            for idx, wval in enumerate(widgets):
                if idx < len(scalar_names):
                    inputs[scalar_names[idx]] = wval

        api[nid] = {"class_type": class_type, "inputs": inputs}

    return api


def normalize_for_prompt(
    workflow: dict[str, Any],
    object_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if is_ui_format(workflow):
        return ui_to_api(workflow, object_info)
    return strip_meta(workflow)


def validate_node_types(
    workflow: dict[str, Any],
    object_info: dict[str, Any],
) -> dict[str, Any]:
    """Check class_types against ComfyUI /object_info."""
    api_wf = normalize_for_prompt(workflow, object_info)
    missing: list[str] = []
    present: list[str] = []
    for _nid, node in api_wf.items():
        if not isinstance(node, dict):
            continue
        ct = node.get("class_type")
        if not ct:
            continue
        if ct in object_info:
            present.append(ct)
        else:
            missing.append(ct)
    unique_missing = sorted(set(missing))
    return {
        "valid": len(unique_missing) == 0,
        "node_count": len(api_wf),
        "present_types": sorted(set(present)),
        "missing_types": unique_missing,
        "message": (
            f"All {len(api_wf)} nodes registered in ComfyUI."
            if not unique_missing
            else f"Missing custom nodes for: {', '.join(unique_missing)}"
        ),
    }


def parse_workflow_json(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)

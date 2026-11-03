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


def api_to_ui(workflow: dict[str, Any]) -> dict[str, Any]:
    """Minimal API -> canvas conversion with topological 2D placement.

    Inverse of ui_to_api for dashboard previews. Computes depth by following
    [node_id, slot] input links; x = depth * 320, y = order * 160.
    """
    api = strip_meta(workflow)
    ids = [k for k, v in api.items() if isinstance(v, dict) and "class_type" in v]
    depth: dict[str, int] = {}

    def _depth(nid: str, seen: set[str] | None = None) -> int:
        if nid in depth:
            return depth[nid]
        seen = seen or set()
        if nid in seen:
            return 0
        seen.add(nid)
        node = api.get(nid, {})
        inputs = node.get("inputs", {}) if isinstance(node, dict) else {}
        parents = [v[0] for v in inputs.values() if isinstance(v, list) and len(v) == 2 and str(v[0]) in api]
        depth[nid] = 0 if not parents else max(_depth(str(p), seen) + 1 for p in parents)
        return depth[nid]

    for nid in ids:
        _depth(str(nid))

    by_depth: dict[int, list[str]] = {}
    for nid in ids:
        by_depth.setdefault(depth[str(nid)], []).append(str(nid))

    nodes: list[dict[str, Any]] = []
    links: list[list[Any]] = []
    link_id = 1
    int_ids = sorted(int(n) for n in ids if str(n).isdigit())
    id_map = {str(n): idx + 1 for idx, n in enumerate(int_ids)}
    id_map.update({n: idx + 1 + len(id_map) for idx, n in enumerate(ids) if n not in id_map})

    for d in sorted(by_depth):
        for order, nid in enumerate(sorted(by_depth[d], key=lambda x: int(x) if x.isdigit() else x)):
            node = api[nid]
            nodes.append(
                {
                    "id": id_map[nid],
                    "type": node.get("class_type"),
                    "pos": [d * 320, order * 160],
                    "inputs": [{"name": k} for k in node.get("inputs", {})],
                    "widgets_values": [
                        v for v in node.get("inputs", {}).values() if not (isinstance(v, list) and len(v) == 2)
                    ],
                }
            )
    for nid in ids:
        node = api[nid]
        for slot_idx, (_name, val) in enumerate(node.get("inputs", {}).items()):
            if isinstance(val, list) and len(val) == 2 and str(val[0]) in id_map:
                links.append([link_id, id_map[str(val[0])], int(val[1]), id_map[nid], slot_idx, "*"])
                link_id += 1

    return {"nodes": nodes, "links": links, "groups": [], "version": 0.4}


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

"""Tests for LongCat-Video 13.6B workflows in comfyops-mcp."""

import json
from pathlib import Path
import pytest

from comfyops_mcp.tools.generate import _MODEL_VRAM_MAP
from comfyops_mcp.comfyui_manager import get_workflow_depot


def test_longcat_workflows_on_disk():
    root = Path(__file__).resolve().parents[1] / "workflows"
    t2v_path = root / "longcat-t2v.json"
    extend_path = root / "longcat-extend.json"

    assert t2v_path.exists(), "longcat-t2v.json missing from workflows/"
    assert extend_path.exists(), "longcat-extend.json missing from workflows/"

    t2v_json = json.loads(t2v_path.read_text(encoding="utf-8"))
    extend_json = json.loads(extend_path.read_text(encoding="utf-8"))

    assert "_meta" in t2v_json
    assert t2v_json["_meta"]["name"] == "LongCat-Video 13.6B Text-to-Video"
    assert t2v_json["_meta"]["model_type"] == "video"

    assert "_meta" in extend_json
    assert extend_json["_meta"]["name"] == "LongCat-Video 13.6B Video Continuation"
    assert extend_json["_meta"]["model_type"] == "video"


def test_longcat_vram_map_entries():
    assert "longcat-t2v" in _MODEL_VRAM_MAP
    assert "longcat-extend" in _MODEL_VRAM_MAP
    assert _MODEL_VRAM_MAP["longcat-t2v"] == 16.0
    assert _MODEL_VRAM_MAP["longcat-extend"] == 16.0


def test_longcat_workflows_in_depot():
    depot = get_workflow_depot()
    depot_ids = {wf["id"] for wf in depot}
    assert "longcat-t2v" in depot_ids
    assert "longcat-extend" in depot_ids

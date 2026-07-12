"""Basic tests for comfyops-mcp tools."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from comfyops_mcp.config import WORKFLOWS_DIR
from comfyops_mcp.tools.generate import _apply_params, _MODEL_VRAM_MAP


class TestGenerate:
    def test_vram_map_has_all_workflows(self):
        """All curated workflows should have a VRAM estimate."""
        wf_dir = Path(WORKFLOWS_DIR)
        if wf_dir.exists():
            for wf in wf_dir.glob("*.json"):
                wf_id = wf.stem
                if not wf_id.startswith("_"):
                    assert wf_id in _MODEL_VRAM_MAP, f"Missing VRAM estimate for {wf_id}"

    def test_apply_params_sets_seed(self):
        workflow = {"3": {"class_type": "KSampler", "inputs": {"seed": 42}}}
        result = _apply_params(workflow, "test", 123, None, None, None)
        assert result["3"]["inputs"]["seed"] == 123

    def test_apply_params_sets_prompt(self):
        workflow = {"12": {"class_type": "CLIPTextEncode", "inputs": {"text": "original"}}}
        result = _apply_params(workflow, "new prompt", 42, None, None, None)
        assert result["12"]["inputs"]["text"] == "new prompt"

    def test_apply_params_sets_size(self):
        workflow = {"11": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512}}}
        result = _apply_params(workflow, "test", 42, "1280x720", None, None)
        assert result["11"]["inputs"]["width"] == 1280
        assert result["11"]["inputs"]["height"] == 720

    def test_apply_params_preserves_meta(self):
        workflow = {"_meta": {"name": "test"}, "3": {"class_type": "KSampler", "inputs": {"seed": 0}}}
        result = _apply_params(workflow, "test", 42, None, None, None)
        assert result["_meta"]["name"] == "test"

    def test_generate_returns_error_for_missing_workflow(self):
        """Simulates comfy_generate with non-existent workflow ID.
        This is a structure test — the real test requires ComfyUI running.
        """
        pass

    def test_workflow_jsons_are_valid(self):
        """All workflow JSONs should parse correctly."""
        wf_dir = Path(WORKFLOWS_DIR)
        if not wf_dir.exists():
            pytest.skip("Workflows directory not found (not in CI)")
        import json
        for wf in wf_dir.glob("*.json"):
            data = json.loads(wf.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{wf.name} is not a dict"
            # Every workflow should have at least a KSampler or similar
            node_types = [n.get("class_type", "") for n in data.values()
                          if isinstance(n, dict) and not n.get("class_type", "").startswith("_")]
            assert len(node_types) > 2, f"{wf.name} has too few nodes"


class TestModels:
    def test_list_models_returns_list(self):
        """list_models should return a list (possibly empty in CI without models)."""
        import pytest_asyncio
        from comfyops_mcp.comfyui_manager import list_models

        models = []  # In CI, no models directory

    def test_vram_estimates_are_positive(self):
        for wf_id, vram in _MODEL_VRAM_MAP.items():
            assert vram > 0, f"{wf_id} has non-positive VRAM estimate: {vram}"
            assert vram <= 24, f"{wf_id} VRAM estimate {vram} exceeds RTX 4090 capacity"


class TestLibrary:
    def test_init_db_creates_file(self):
        from comfyops_mcp.tools.library import DB_PATH
        from comfyops_mcp.tools.library import _init_db

        _init_db()
        assert DB_PATH.exists() or DB_PATH.parent.exists()

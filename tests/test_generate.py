"""Tests for comfy_generate helpers and tool (mocked ComfyUI)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from comfyops_mcp.tools.generate import _MODEL_VRAM_MAP, _apply_params, register_tools
from tests.conftest import capture_tool

CURATED = {
    "flux-klein-t2i",
    "sdxl-lora-t2i",
    "wan22-t2v",
    "esrgan-upscale",
    "flux-inpaint",
}


class TestApplyParams:
    def test_seed(self):
        wf = {"3": {"class_type": "KSampler", "inputs": {"seed": 1}}}
        out = _apply_params(wf, "p", 99, None, None, None)
        assert out["3"]["inputs"]["seed"] == 99

    def test_prompt_and_negative(self):
        wf = {
            "12": {"class_type": "CLIPTextEncode", "inputs": {"text": "a"}},
            "13": {"class_type": "CLIPTextEncode", "inputs": {"text": "b"}},
        }
        out = _apply_params(wf, "pos", 1, None, "neg", None)
        assert out["12"]["inputs"]["text"] == "pos"
        assert out["13"]["inputs"]["text"] == "neg"

    def test_size(self):
        wf = {"11": {"class_type": "EmptyLatentImage", "inputs": {"width": 64, "height": 64}}}
        out = _apply_params(wf, "p", 1, "1280x720", None, None)
        assert out["11"]["inputs"]["width"] == 1280
        assert out["11"]["inputs"]["height"] == 720

    def test_preserves_meta(self):
        wf = {"_meta": {"name": "x"}, "3": {"class_type": "KSampler", "inputs": {"seed": 0}}}
        out = _apply_params(wf, "p", 1, None, None, None)
        assert out["_meta"]["name"] == "x"

    def test_does_not_mutate_input(self):
        wf = {"3": {"class_type": "KSampler", "inputs": {"seed": 1}}}
        _apply_params(wf, "p", 42, None, None, None)
        assert wf["3"]["inputs"]["seed"] == 1


class TestVramMap:
    def test_curated_workflows_on_disk_have_estimates(self):
        root = Path(__file__).resolve().parents[1] / "workflows"
        on_disk = {p.stem for p in root.glob("*.json")}
        missing = CURATED - on_disk
        assert not missing, f"curated workflows missing from disk: {missing}"
        for wf_id in on_disk:
            assert wf_id in _MODEL_VRAM_MAP, f"missing VRAM map for {wf_id}"

    def test_estimates_reasonable(self):
        for wf_id, gb in _MODEL_VRAM_MAP.items():
            assert 0 < gb <= 24, f"{wf_id}={gb}"

    def test_known_curated_subset(self):
        assert CURATED.issubset(_MODEL_VRAM_MAP.keys())


class TestComfyGenerate:
    @pytest.fixture
    def tool(self):
        return capture_tool(register_tools, "comfy_generate")

    async def test_missing_workflow(self, tool, isolated_config, mock_comfy_client):
        with patch(
            "comfyops_mcp.tools.generate.ensure_comfyui_running",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ):
            result = await tool(
                operation="image",
                workflow_id="does-not-exist",
                prompt="hi",
            )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    async def test_vram_blocks(self, tool, isolated_config, mock_comfy_client):
        with patch(
            "comfyops_mcp.tools.generate.ensure_comfyui_running",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ):
            with patch(
                "comfyops_mcp.tools.generate.check_vram",
                new_callable=AsyncMock,
                return_value={"ok": False, "error": "low vram", "vram_free": 1, "required": 6},
            ):
                result = await tool(operation="image", workflow_id="test-workflow", prompt="x")
        assert result["success"] is False
        assert result["error_type"] == "vram"

    async def test_happy_path(self, tool, isolated_config, mock_comfy_client):
        with patch(
            "comfyops_mcp.tools.generate.ensure_comfyui_running",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ):
            with patch(
                "comfyops_mcp.tools.generate.check_vram",
                new_callable=AsyncMock,
                return_value={"ok": True, "vram_free": 10, "required": 6},
            ):
                with patch(
                    "comfyops_mcp.tools.generate.get_object_info",
                    new_callable=AsyncMock,
                    return_value={"ok": True, "object_info": {"KSampler": {}, "CheckpointLoaderSimple": {}}},
                ):
                    with patch(
                        "comfyops_mcp.tools.generate.ensure_workflow_nodes",
                        new_callable=AsyncMock,
                        return_value={"ok": True, "valid": True, "installed": []},
                    ):
                        with patch(
                            "comfyops_mcp.tools.generate.queue_prompt",
                            new_callable=AsyncMock,
                            return_value={"ok": True, "prompt_id": "abc"},
                        ):
                            with patch(
                                "comfyops_mcp.tools.generate.wait_for_result",
                                new_callable=AsyncMock,
                                return_value={
                                    "ok": True,
                                    "outputs": [{"filename": "x.png"}],
                                    "prompt_id": "abc",
                                },
                            ):
                                result = await tool(
                                    operation="image",
                                    workflow_id="test-workflow",
                                    prompt="a cat",
                                    seed=7,
                                )
        assert result["success"] is True
        assert result["seed"] == 7
        assert result["prompt_id"] == "abc"
        assert len(result["outputs"]) == 1

    async def test_queue_failure(self, tool, isolated_config, mock_comfy_client):
        with patch(
            "comfyops_mcp.tools.generate.ensure_comfyui_running",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ):
            with patch(
                "comfyops_mcp.tools.generate.check_vram",
                new_callable=AsyncMock,
                return_value={"ok": True, "vram_free": 10, "required": 6},
            ):
                with patch(
                    "comfyops_mcp.tools.generate.get_object_info",
                    new_callable=AsyncMock,
                    return_value={"ok": True, "object_info": {}},
                ):
                    with patch(
                        "comfyops_mcp.tools.generate.ensure_workflow_nodes",
                        new_callable=AsyncMock,
                        return_value={"ok": True, "valid": True},
                    ):
                        with patch(
                            "comfyops_mcp.tools.generate.queue_prompt",
                            new_callable=AsyncMock,
                            return_value={"ok": False, "error": "bad graph"},
                        ):
                            result = await tool(operation="image", workflow_id="test-workflow", prompt="x")
        assert result["success"] is False
        assert result["error_type"] == "comfyui"

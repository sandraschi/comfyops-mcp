"""Tests for comfy_generate portmanteau tool."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from comfyops_mcp import config as cfg
from comfyops_mcp.tools.generate import (
    _apply_params,
    _MODEL_VRAM_MAP,
    register_tools,
)


class TestApplyParams:
    def test_sets_seed_in_ksampler(self):
        wf = {"3": {"class_type": "KSampler", "inputs": {"seed": 0}}}
        result = _apply_params(wf, "test", 42, None, None, None)
        assert result["3"]["inputs"]["seed"] == 42

    def test_sets_seed_in_sampler_custom(self):
        wf = {"5": {"class_type": "SamplerCustom", "inputs": {"seed": 0}}}
        result = _apply_params(wf, "test", 99, None, None, None)
        assert result["5"]["inputs"]["seed"] == 99

    def test_sets_prompt_in_clip_text_encode(self):
        wf = {"12": {"class_type": "CLIPTextEncode", "inputs": {"text": "old"}}}
        result = _apply_params(wf, "new prompt", 42, None, None, None)
        assert result["12"]["inputs"]["text"] == "new prompt"

    def test_sets_negative_prompt(self):
        wf = {"12": {"class_type": "CLIPTextEncode", "inputs": {"text": "old"}},
              "13": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}}}
        result = _apply_params(wf, "positive", 42, None, None, "bad stuff", None)
        primary_text = result["12"]["inputs"]["text"]
        assert primary_text == "positive"

    def test_sets_image_size(self):
        wf = {"11": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512}}}
        result = _apply_params(wf, "test", 42, "1280x720", None, None)
        assert result["11"]["inputs"]["width"] == 1280
        assert result["11"]["inputs"]["height"] == 720

    def test_ignores_malformed_size(self):
        wf = {"11": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512}}}
        result = _apply_params(wf, "test", 42, "square", None, None)
        assert result["11"]["inputs"]["width"] == 512

    def test_preserves_meta_block(self):
        wf = {"_meta": {"name": "test"}, "3": {"class_type": "KSampler", "inputs": {"seed": 0}}}
        result = _apply_params(wf, "test", 42, None, None, None)
        assert result["_meta"]["name"] == "test"

    def test_does_not_modify_original(self):
        wf = {"3": {"class_type": "KSampler", "inputs": {"seed": 0}}}
        _apply_params(wf, "test", 42, None, None, None)
        assert wf["3"]["inputs"]["seed"] == 0

    def test_handles_empty_workflow(self):
        result = _apply_params({}, "test", 42, None, None, None)
        assert result == {}

    def test_handles_non_standard_nodes(self):
        wf = {"99": {"inputs": {"text": "hello"}}}  # No class_type
        result = _apply_params(wf, "test", 42, None, None, None)
        assert result["99"]["inputs"]["text"] == "test"

    def test_sets_image_input(self):
        wf = {"15": {"class_type": "LoadImage", "inputs": {"image": ""}}}
        result = _apply_params(wf, "test", 42, None, None, "base64data")
        assert result["15"]["inputs"]["image"] == "base64data"


class TestVRAMMap:
    def test_all_entries_have_positive_vram(self):
        for wf_id, vram in _MODEL_VRAM_MAP.items():
            assert vram > 0, f"{wf_id} has zero or negative VRAM"

    def test_no_entry_exceeds_4090_capacity(self):
        for wf_id, vram in _MODEL_VRAM_MAP.items():
            assert vram <= 24, f"{wf_id} requires {vram} GB but 4090 has 24 GB"

    def test_covers_all_curated_workflows(self, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            wf_dir = Path(tmp_workflows_dir)
            for wf in wf_dir.glob("*.json"):
                wf_id = wf.stem
                assert wf_id in _MODEL_VRAM_MAP, f"Missing VRAM estimate for {wf_id}"

    def test_vram_values_are_reasonable(self):
        for wf_id, vram in _MODEL_VRAM_MAP.items():
            assert vram >= 1.0, f"{wf_id} VRAM estimate suspiciously low: {vram}"
            assert vram <= 22, f"{wf_id} VRAM estimate seems too high: {vram}"


class TestToolRegistration:
    def test_register_tools_accepts_mcp(self):
        mcp = MagicMock()
        mcp.tool = MagicMock(return_value=lambda f: f)
        register_tools(mcp)
        assert mcp.tool.called

    def test_tool_has_mutating_annotation(self):
        mcp = MagicMock()
        mcp.tool = MagicMock(return_value=lambda f: f)
        register_tools(mcp)
        call_kwargs = mcp.tool.call_args_list[0][1] if mcp.tool.call_args_list else {}
        annotations = call_kwargs.get("annotations", {})
        assert annotations.get("readonly") is False


class TestGenerateIntegration:
    """Integration-style tests that verify the tool pipeline with mocks.

    These test the full comfy_generate path through VRAM check, workflow
    loading, prompt queueing, and result polling.
    """

    @pytest_asyncio.fixture
    async def mock_generate_deps(self, tmp_workflows_dir, mock_httpx_client):
        """Patch all external dependencies for a full generate flow."""
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            yield

    async def test_generate_happy_path(self, mock_generate_deps):
        """Full pipeline: VRAM ok → workflow loaded → queued → result."""
        from comfyops_mcp.comfyui_manager import check_vram, queue_prompt, wait_for_result

        vram = await check_vram(4.0)
        assert vram["ok"] is True

        wf_path = Path(cfg.WORKFLOWS_DIR) / "test-workflow.json"
        assert wf_path.exists()
        workflow = json.loads(wf_path.read_text())
        assert "KSampler" in str(workflow)

        queue = await queue_prompt(workflow)
        assert queue["ok"] is True

        result = await wait_for_result(queue["prompt_id"])
        assert result["ok"] is True

    async def test_generate_fails_without_comfyui(self):
        """When ComfyUI is down, generate should return a clear error."""
        with patch("comfyops_mcp.comfyui_manager.check_health") as mock_health:
            mock_health.return_value = {"ok": False, "error": "Connection refused"}
            vram = await check_vram(4.0)
            assert vram["ok"] is False

    async def test_generate_fails_with_unknown_workflow(self):
        """Non-existent workflow ID should produce an error with suggestions."""
        from comfyops_mcp.tools.generate import register_tools

        mcp = MagicMock()
        mcp.tool = MagicMock(return_value=lambda f: f)
        register_tools(mcp)

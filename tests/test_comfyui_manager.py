"""Tests for ComfyUI sidecar manager — health checks, VRAM, prompts, models."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from comfyops_mcp import config as cfg
from comfyops_mcp.comfyui_manager import (
    check_health,
    check_vram,
    get_client,
    get_workflow_depot,
    list_models,
    queue_prompt,
    wait_for_result,
)


class TestComfyUIConnection:
    async def test_check_health_success(self, mock_httpx_client):
        result = await check_health()
        assert result["ok"] is True
        assert result["comfyui_version"] == "0.3.0"

    async def test_check_health_connect_error(self):
        with patch("comfyops_mcp.comfyui_manager.get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_get.return_value = mock_client
            result = await check_health()
            assert result["ok"] is False
            assert "Connection refused" in result["error"]

    async def test_check_health_http_error(self, mock_httpx_client):
        mock_response = MagicMock(status_code=503, text=lambda: "Service Unavailable")
        mock_httpx_client.get.return_value = mock_response
        result = await check_health()
        assert result["ok"] is False
        assert "HTTP 503" in result["error"]

    async def test_check_health_reports_vram(self, mock_httpx_client):
        result = await check_health()
        assert result["vram_free"] == 8 * 1024**3
        assert result["vram_total"] == 24 * 1024**3


class TestVRAM:
    async def test_check_vram_sufficient(self, mock_httpx_client):
        result = await check_vram(4.0)
        assert result["ok"] is True
        assert result["vram_free"] == 8.0
        assert result["required"] == 4.0

    async def test_check_vram_insufficient(self, mock_httpx_client):
        with patch("comfyops_mcp.comfyui_manager.check_health") as mock_health:
            mock_health.return_value = {
                "ok": True,
                "vram_free": 2 * 1024**3,
                "vram_total": 24 * 1024**3,
                "cuda_devices": [{"name": "RTX 4090"}],
                "comfyui_version": "0.3.0",
            }
            result = await check_vram(8.0)
            assert result["ok"] is False
            assert "Only 2.0 GB VRAM free" in result["error"]

    async def test_check_vram_no_comfyui(self):
        with patch("comfyops_mcp.comfyui_manager.check_health") as mock_health:
            mock_health.return_value = {"ok": False, "error": "Not reachable"}
            result = await check_vram(4.0)
            assert result["ok"] is False


class TestWorkflowDepot:
    def test_get_workflow_depot_returns_list(self, patch_config):
        depot = get_workflow_depot()
        assert len(depot) >= 1
        assert depot[0]["id"] == "test-workflow"
        assert depot[0]["name"] == "Test Workflow"

    def test_get_workflow_depot_includes_metadata(self, patch_config):
        depot = get_workflow_depot()
        wf = next(w for w in depot if w["id"] == "test-workflow")
        assert wf["model_type"] == "image"
        assert "prompt" in wf["params"]
        assert "docs" in wf

    def test_get_workflow_depot_empty_dir(self):
        depot = get_workflow_depot()
        assert depot == []


class TestPromptQueue:
    async def test_queue_prompt_success(self, mock_httpx_client):
        workflow = {"3": {"class_type": "KSampler", "inputs": {"seed": 42}}}
        result = await queue_prompt(workflow)
        assert result["ok"] is True
        assert result["prompt_id"] == "test-prompt-001"

    async def test_queue_prompt_http_error(self, mock_httpx_client):
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=MagicMock(status_code=400, text=lambda: '{"error": "Invalid prompt"}')
        )
        result = await queue_prompt({"bad": "workflow"})
        assert result["ok"] is False

    async def test_queue_prompt_no_prompt_id(self, mock_httpx_client):
        mock_httpx_client.post.side_effect = None
        mock_response = MagicMock(status_code=200, json=lambda: {"number": 1})
        mock_httpx_client.post.return_value = mock_response
        result = await queue_prompt({"test": "data"})
        assert result["ok"] is False

    async def test_queue_prompt_connection_error(self):
        with patch("comfyops_mcp.comfyui_manager.get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_get.return_value = mock_client
            result = await queue_prompt({"test": "data"})
            assert result["ok"] is False


class TestResultPolling:
    async def test_wait_for_result_success(self, mock_httpx_client):
        result = await wait_for_result("test-prompt-001", timeout=10)
        assert result["ok"] is True
        assert len(result["outputs"]) >= 1
        assert result["outputs"][0]["filename"] == "test_00001_.png"

    async def test_wait_for_result_timeout(self, mock_httpx_client):
        mock_response = MagicMock(status_code=200, json=lambda: {})
        mock_httpx_client.get.return_value = mock_response
        result = await wait_for_result("stuck-prompt", timeout=1)
        assert result["ok"] is False
        assert "Timeout" in result["error"]

    async def test_wait_for_result_http_error(self, mock_httpx_client):
        mock_response = MagicMock(status_code=500, text=lambda: "Server Error")
        mock_httpx_client.get.return_value = mock_response
        result = await wait_for_result("error-prompt", timeout=1)
        assert result["ok"] is False


class TestListModels:
    async def test_list_models_returns_files(self, tmp_models_dir):
        with patch.object(cfg, "MODELS_DIR", tmp_models_dir):
            models = await list_models()
            assert len(models) >= 1
            assert any("flux_test" in m["name"] for m in models)

    async def test_list_models_reports_size(self, tmp_models_dir):
        with patch.object(cfg, "MODELS_DIR", tmp_models_dir):
            models = await list_models()
            flux = next(m for m in models if "flux_test" in m["name"])
            assert flux["size_mb"] == 1.0  # 1 MB dummy file

    async def test_list_models_empty_dir(self, tmp_path):
        empty = tmp_path / "nope"
        empty.mkdir()
        with patch.object(cfg, "MODELS_DIR", str(empty)):
            models = await list_models()
            assert models == []

    async def test_list_models_nonexistent_dir(self):
        with patch.object(cfg, "MODELS_DIR", "Z:\\does_not_exist"):
            models = await list_models()
            assert models == []


class TestModelsEdgeCases:
    async def test_list_models_rejects_binaries(self, tmp_models_dir):
        """Model scanning should only pick known extensions."""
        import os
        stray = os.path.join(tmp_models_dir, "readme.txt")
        Path(stray).write_text("not a model")
        with patch.object(cfg, "MODELS_DIR", tmp_models_dir):
            models = await list_models()
            txt = [m for m in models if m["name"] == "readme"]
            assert len(txt) == 0

    async def test_list_models_scans_subdirs(self, tmp_models_dir):
        sub = Path(tmp_models_dir) / "checkpoints"
        sub.mkdir()
        (sub / "deep_model.safetensors").write_bytes(b"y" * 512)
        with patch.object(cfg, "MODELS_DIR", tmp_models_dir):
            models = await list_models()
            names = [m["name"] for m in models]
            assert "deep_model" in names

"""Tests for comfy_models portmanteau tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from comfyops_mcp import config as cfg
from comfyops_mcp.tools.models_tool import register_tools


@pytest_asyncio.fixture
async def models_tool(tmp_models_dir):
    mcp = MagicMock()
    decorated = {}

    def capture_decorator(**kwargs):
        def wrapper(f):
            decorated[f.__name__] = (f, kwargs)
            return f
        return wrapper

    mcp.tool = capture_decorator
    register_tools(mcp)
    fn, _ = decorated.get("comfy_models", (None, None))
    assert fn is not None
    return fn


class TestModelsListInstalled:
    async def test_list_installed_returns_models(self, models_tool, tmp_models_dir):
        with patch.object(cfg, "MODELS_DIR", tmp_models_dir):
            result = await models_tool(operation="list_installed")
        assert result["success"] is True
        assert result["count"] >= 1
        assert "flux_test" in str(result["models"])

    async def test_list_installed_empty_without_models(self, models_tool, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        with patch.object(cfg, "MODELS_DIR", str(empty)):
            result = await models_tool(operation="list_installed")
        assert result["count"] == 0

    async def test_list_installed_reports_total_size(self, models_tool, tmp_models_dir):
        with patch.object(cfg, "MODELS_DIR", tmp_models_dir):
            result = await models_tool(operation="list_installed")
        assert result["total_size_gb"] > 0


class TestModelsCheckVRAM:
    async def test_check_vram_ok(self, models_tool, mock_httpx_client):
        result = await models_tool(operation="check_vram", model_vram_gb=4.0)
        assert result["success"] is True
        assert result["vram_free"] > 0

    async def test_check_vram_without_param(self, models_tool, mock_httpx_client):
        result = await models_tool(operation="check_vram")
        assert result["success"] is True

    async def test_check_vram_insufficient(self, models_tool, mock_httpx_client):
        with patch("comfyops_mcp.tools.models_tool.check_vram") as mock_check:
            mock_check.return_value = {
                "ok": False, "vram_free": 2.0, "required": 8.0,
                "error": "Only 2.0 GB VRAM free, need ~8.0 GB",
            }
            result = await models_tool(operation="check_vram", model_vram_gb=8.0)
        assert result["success"] is False
        assert "vram" in result.get("error_type", "")

    async def test_check_vram_no_comfyui(self, models_tool):
        with patch("comfyops_mcp.tools.models_tool.check_vram") as mock_check:
            mock_check.return_value = {"ok": False, "error": "ComfyUI not reachable"}
            result = await models_tool(operation="check_vram")
        assert result["success"] is False


class TestModelsHealth:
    async def test_health_returns_comfyui_version(self, models_tool, mock_httpx_client):
        result = await models_tool(operation="health")
        assert result["success"] is True
        assert result["comfyui_version"] == "0.3.0"

    async def test_health_reports_vram(self, models_tool, mock_httpx_client):
        result = await models_tool(operation="health")
        assert result["vram_free_gb"] > 0
        assert result["vram_total_gb"] == 24.0

    async def test_health_connection_failure(self, models_tool):
        with patch("comfyops_mcp.tools.models_tool.check_health") as mock_health:
            mock_health.return_value = {"ok": False, "error": "Connection refused"}
            result = await models_tool(operation="health")
        assert result["success"] is False
        assert "suggestions" in result

    async def test_health_reports_cuda_devices(self, models_tool, mock_httpx_client):
        result = await models_tool(operation="health")
        assert result["cuda_devices"] >= 1


class TestModelsErrorHandling:
    async def test_unknown_operation(self, models_tool):
        result = await models_tool(operation="reboot")
        assert result["success"] is False
        assert "Unknown operation" in result["error"]

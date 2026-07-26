"""Tests for comfy_models portmanteau."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from comfyops_mcp.tools.models_tool import register_tools
from tests.conftest import capture_tool


@pytest.fixture
def tool():
    return capture_tool(register_tools, "comfy_models")


class TestListInstalled:
    async def test_lists_files(self, tool, isolated_config):
        result = await tool(operation="list_installed")
        assert result["success"] is True
        assert result["count"] >= 2
        assert all(m["size_mb"] > 0 for m in result["models"])
        names = {m["name"] for m in result["models"]}
        assert "flux_test" in names


class TestCheckVram:
    async def test_ok(self, tool, isolated_config, mock_comfy_client):
        result = await tool(operation="check_vram", model_vram_gb=4.0)
        assert result["success"] is True
        assert result["vram_free"] >= 4.0

    async def test_offline(self, tool, isolated_config):
        with patch(
            "comfyops_mcp.tools.models_tool.check_vram",
            new_callable=AsyncMock,
            return_value={"ok": False, "error": "down", "vram_free": 0, "required": 4.0},
        ):
            result = await tool(operation="check_vram")
        assert result["success"] is False
        assert result["error_type"] == "vram"
        assert result["vram_free"] == 0


class TestHealth:
    async def test_ok(self, tool, isolated_config, mock_comfy_client):
        result = await tool(operation="health")
        assert result["success"] is True
        assert result["comfyui_version"] == "0.3.0"
        assert result["vram_total_gb"] == 24.0

    async def test_offline(self, tool, isolated_config):
        with patch(
            "comfyops_mcp.tools.models_tool.check_health",
            new_callable=AsyncMock,
            return_value={"ok": False, "error": "unreachable"},
        ):
            result = await tool(operation="health")
        assert result["success"] is False
        assert result["error_type"] == "connection"

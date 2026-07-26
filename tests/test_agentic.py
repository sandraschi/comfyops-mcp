"""Tests for comfy_agentic_assist."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from comfyops_mcp.tools.agentic import register_tools
from tests.conftest import capture_tool


@pytest.fixture
def tool():
    return capture_tool(register_tools, "comfy_agentic_assist")


class TestAgentic:
    async def test_no_ctx(self, tool):
        result = await tool(goal="cyberpunk city")
        assert result["success"] is False
        assert result["error_type"] == "sampling_unavailable"

    async def test_sampling_ok(self, tool):
        ctx = MagicMock()
        ctx.sample = AsyncMock(return_value="workflow_id: flux-klein-t2i")
        result = await tool(goal="aerial cyberpunk shot", ctx=ctx)
        assert result["success"] is True
        assert "flux-klein" in result["agent_plan"]

    async def test_sampling_error(self, tool):
        ctx = MagicMock()
        ctx.sample = AsyncMock(side_effect=RuntimeError("no sampler"))
        result = await tool(goal="x", ctx=ctx)
        assert result["success"] is False
        assert result["error_type"] == "sampling_error"

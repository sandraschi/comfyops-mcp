"""Tests for comfy_agentic_assist tool — SEP-1577 sampling."""

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from comfyops_mcp.tools.agentic import register_tools


@pytest_asyncio.fixture
async def agentic_tool():
    mcp = MagicMock()
    decorated = {}

    def capture_decorator(**kwargs):
        def wrapper(f):
            decorated[f.__name__] = (f, kwargs)
            return f
        return wrapper

    mcp.tool = capture_decorator
    register_tools(mcp)
    fn, _ = decorated.get("comfy_agentic_assist", (None, None))
    assert fn is not None
    return fn


class TestAgenticAssist:
    async def test_returns_sampling_unavailable_without_ctx(self, agentic_tool):
        result = await agentic_tool(goal="make a picture of a cat")
        assert result["success"] is False
        assert result["error_type"] == "sampling_unavailable"
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    async def test_suggestion_references_manual_tools(self, agentic_tool):
        result = await agentic_tool(goal="test")
        suggestion = result["suggestions"][0]
        assert "comfy_workflows" in suggestion
        assert "comfy_generate" in suggestion

    async def test_sampling_with_context(self, agentic_tool):
        mock_ctx = AsyncMock()
        mock_ctx.sample = AsyncMock(return_value="Use flux-klein-t2i with prompt 'cat'")

        result = await agentic_tool(goal="make a picture", ctx=mock_ctx)
        assert result["success"] is True
        assert mock_ctx.sample.called

    async def test_sampling_passes_goal(self, agentic_tool):
        mock_ctx = AsyncMock()
        mock_ctx.sample = AsyncMock(return_value="plan result")

        await agentic_tool(goal="cyberpunk city at night", ctx=mock_ctx)
        call_args = mock_ctx.sample.call_args
        assert call_args is not None
        assert "cyberpunk" in str(call_args[0])

    async def test_sampling_error_falls_back(self, agentic_tool):
        mock_ctx = AsyncMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("API error"))

        result = await agentic_tool(goal="test", ctx=mock_ctx)
        assert result["success"] is False
        assert result["error_type"] == "sampling_error"

    async def test_empty_goal_still_works(self, agentic_tool):
        mock_ctx = AsyncMock()
        mock_ctx.sample = AsyncMock(return_value="plan")
        result = await agentic_tool(goal="", ctx=mock_ctx)
        assert result["success"] is True

"""Tests for ComfyUI-Manager install resolution."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from comfyops_mcp.manager_install import (
    _invert_mappings,
    packs_from_workflow_meta,
    resolve_packages_for_missing,
)
from comfyops_mcp.tools.nodes_tool import register_tools
from tests.conftest import capture_tool


class TestMappings:
    def test_invert_mappings(self):
        raw = {"ComfyUI-Impact-Pack": [["ImpactInt", "display"]], "Other": ["SimpleNode"]}
        inv = _invert_mappings(raw)
        assert inv["ImpactInt"] == "ComfyUI-Impact-Pack"
        assert inv["SimpleNode"] == "Other"

    def test_packs_from_meta(self):
        wf = {
            "_meta": {
                "required_packs": ["ComfyUI-VideoHelperSuite"],
                "nodes": [{"name": "ComfyUI-Impact-Pack", "version": "1.0"}],
            }
        }
        packs = packs_from_workflow_meta(wf)
        assert "ComfyUI-VideoHelperSuite" in packs
        assert "ComfyUI-Impact-Pack" in packs

    def test_resolve_packages(self):
        resolved = resolve_packages_for_missing(
            ["ImpactInt", "UnknownNode"],
            class_to_pack={"ImpactInt": "ComfyUI-Impact-Pack"},
        )
        assert resolved["packages"] == ["ComfyUI-Impact-Pack"]
        assert resolved["mapped"]["ImpactInt"] == "ComfyUI-Impact-Pack"
        assert "UnknownNode" in resolved["unmapped_types"]


class TestComfyNodesTool:
    @pytest.fixture
    def tool(self):
        return capture_tool(register_tools, "comfy_nodes")

    async def test_status(self, tool):
        result = await tool(operation="status")
        assert result["success"] is True
        assert "manager_installed" in result

    async def test_resolve(self, tool):
        with patch(
            "comfyops_mcp.tools.nodes_tool.fetch_manager_catalog",
            new_callable=AsyncMock,
            return_value={"ok": True, "class_to_pack": {"ImpactInt": "ComfyUI-Impact-Pack"}},
        ):
            result = await tool(operation="resolve", missing_types="ImpactInt,Foo")
        assert result["success"] is True
        assert "ComfyUI-Impact-Pack" in result["packages"]

"""Tests for comfy_comic - generate_panel validation + PIL strip assembly."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from comfyops_mcp.tools.comics import register_tools
from tests.conftest import capture_tool


@pytest.fixture
def tool():
    return capture_tool(register_tools, "comfy_comic")


def _make_png(path: Path, color=(200, 30, 30), size=(64, 64)):
    img = Image.new("RGB", size, color=color)
    img.save(path, format="PNG")
    return str(path)


class TestAssemble:
    async def test_horizontal_strip(self, tool, tmp_path: Path, isolated_config):
        a = _make_png(tmp_path / "a.png", color=(200, 30, 30))
        b = _make_png(tmp_path / "b.png", color=(30, 200, 30))
        result = await tool(operation="assemble_strip", panel_paths=[a, b])
        assert result["success"] is True
        assert Path(result["strip_path"]).exists()
        assert result["dimensions"][0] > 64

    async def test_grid_requires_four(self, tool, tmp_path: Path, isolated_config):
        a = _make_png(tmp_path / "a.png")
        result = await tool(operation="assemble_strip", panel_paths=[a], layout="grid_2x2")
        assert result["success"] is False

    async def test_grid_ok(self, tool, tmp_path: Path, isolated_config):
        paths = [_make_png(tmp_path / f"p{i}.png", color=(i * 40, 100, 100)) for i in range(4)]
        result = await tool(operation="assemble_strip", panel_paths=paths, layout="grid_2x2")
        assert result["success"] is True
        assert result["dimensions"][0] > 0

    async def test_requires_paths(self, tool, isolated_config):
        result = await tool(operation="assemble_strip", panel_paths=[])
        assert result["success"] is False


class TestGenerateValidation:
    async def test_requires_prompt(self, tool, isolated_config):
        result = await tool(operation="generate_panel", prompt=None)
        assert result["success"] is False

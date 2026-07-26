"""Tests for comfy_library SQLite portmanteau."""

from __future__ import annotations

import gc
import sqlite3

import pytest

from comfyops_mcp.tools import library as lib
from comfyops_mcp.tools.library import register_tools
from tests.conftest import capture_tool


@pytest.fixture
def tool(isolated_config):
    yield capture_tool(register_tools, "comfy_library")
    gc.collect()


class TestInitAndRecord:
    def test_init_creates_db(self, isolated_config):
        lib._init_db()
        path = lib._db_path()
        assert path.exists()
        with sqlite3.connect(str(path)) as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='generations'").fetchall()
        assert rows

    async def test_record_requires_prompt_id(self, tool, isolated_config):
        result = await tool(operation="record")
        assert result["success"] is False

    async def test_record_and_recent(self, tool, isolated_config):
        rec = await tool(
            operation="record",
            prompt_id="p1",
            workflow_id="test-workflow",
            prompt_text="a cat surfing",
            seed_val=42,
            model="flux",
            outputs='[{"filename":"a.png"}]',
        )
        assert rec["success"] is True

        recent = await tool(operation="recent", limit=10)
        assert recent["success"] is True
        assert len(recent["generations"]) == 1
        assert recent["generations"][0]["prompt"] == "a cat surfing"
        assert recent["generations"][0]["seed"] == 42

    async def test_record_idempotent(self, tool, isolated_config):
        await tool(operation="record", prompt_id="dup", prompt_text="once")
        await tool(operation="record", prompt_id="dup", prompt_text="twice")
        recent = await tool(operation="recent")
        assert len(recent["generations"]) == 1


class TestSearch:
    async def test_finds_prompt(self, tool, isolated_config):
        await tool(operation="record", prompt_id="s1", prompt_text="neon cityscape")
        await tool(operation="record", prompt_id="s2", prompt_text="quiet forest")
        found = await tool(operation="search", query="neon")
        assert found["success"] is True
        assert len(found["generations"]) == 1
        assert "neon" in found["generations"][0]["prompt"]

    async def test_requires_query(self, tool, isolated_config):
        result = await tool(operation="search")
        assert result["success"] is False

    async def test_recent_limit(self, tool, isolated_config):
        for i in range(5):
            await tool(operation="record", prompt_id=f"r{i}", prompt_text=f"p{i}")
        recent = await tool(operation="recent", limit=2)
        assert len(recent["generations"]) == 2

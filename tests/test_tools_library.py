"""Tests for comfy_library portmanteau tool — SQLite-backed generation history."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from comfyops_mcp import config as cfg
from comfyops_mcp.tools.library import register_tools, DB_PATH, _init_db


@pytest_asyncio.fixture
async def library_tool(tmp_data_dir):
    mcp = MagicMock()
    decorated = {}

    def capture_decorator(**kwargs):
        def wrapper(f):
            decorated[f.__name__] = (f, kwargs)
            return f
        return wrapper

    mcp.tool = capture_decorator
    register_tools(mcp)
    fn, _ = decorated.get("comfy_library", (None, None))
    assert fn is not None
    return fn


class TestLibraryInit:
    def test_init_db_creates_file(self, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            _init_db()
            assert Path(tmp_data_dir, "library.sqlite3").exists()

    def test_init_db_idempotent(self, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            _init_db()
            _init_db()  # Second call should not crash


class TestLibraryRecord:
    async def test_record_creates_entry(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            result = await library_tool(
                operation="record",
                prompt_id="test-001",
                workflow_id="flux-klein-t2i",
                prompt_text="a test image",
                seed_val=42,
                model="flux_klein",
                outputs='[{"filename":"test.png"}]',
            )
        assert result["success"] is True

    async def test_record_duplicate_is_idempotent(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            await library_tool(
                operation="record", prompt_id="dup-001",
                workflow_id="test", prompt_text="first",
            )
            result = await library_tool(
                operation="record", prompt_id="dup-001",
                workflow_id="test", prompt_text="second",
            )
            assert result["success"] is True

    async def test_record_requires_prompt_id(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            result = await library_tool(operation="record")
        assert result["success"] is False
        assert "prompt_id required" in result["error"]

    async def test_record_then_recent_shows_it(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            await library_tool(
                operation="record", prompt_id="recent-test",
                workflow_id="test-wf", prompt_text="show me",
            )
            recent = await library_tool(operation="recent")
        assert recent["success"] is True
        prompts = [g["prompt_id"] for g in recent["generations"]]
        assert "recent-test" in prompts


class TestLibraryRecent:
    async def test_recent_returns_list(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            result = await library_tool(operation="recent")
        assert result["success"] is True
        assert isinstance(result["generations"], list)

    async def test_recent_respects_limit(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            for i in range(5):
                await library_tool(
                    operation="record", prompt_id=f"limit-{i:03d}",
                    workflow_id="test", prompt_text=f"gen {i}",
                )
            result = await library_tool(operation="recent", limit=2)
        assert len(result["generations"]) <= 2

    async def test_recent_ordered_by_date_desc(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            await library_tool(
                operation="record", prompt_id="first",
                workflow_id="test", prompt_text="oldest",
            )
            await library_tool(
                operation="record", prompt_id="second",
                workflow_id="test", prompt_text="newest",
            )
            result = await library_tool(operation="recent")
        if len(result["generations"]) >= 2:
            assert result["generations"][0]["prompt_id"] == "second"

    async def test_recent_empty_when_no_generations(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            result = await library_tool(operation="recent")
        assert result["generations"] == []


class TestLibrarySearch:
    async def test_search_finds_matching_prompt(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            await library_tool(
                operation="record", prompt_id="search-me",
                workflow_id="test", prompt_text="a cat wearing a hat",
            )
            result = await library_tool(operation="search", query="cat")
        assert result["success"] is True
        assert len(result["generations"]) >= 1

    async def test_search_no_match(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            result = await library_tool(operation="search", query="zzz_nonexistent")
        assert result["generations"] == []

    async def test_search_requires_query(self, library_tool, tmp_data_dir):
        with patch.object(cfg, "DATA_DIR", tmp_data_dir):
            result = await library_tool(operation="search")
        assert result["success"] is False
        assert "query required" in result["error"]


class TestLibraryErrorHandling:
    async def test_unknown_operation(self, library_tool):
        result = await library_tool(operation="delete_all")
        assert result["success"] is False
        assert "Unknown operation" in result["error"]

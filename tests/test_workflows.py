"""Tests for comfy_workflows portmanteau."""

from __future__ import annotations

import json

import pytest

from comfyops_mcp.tools.workflows import register_tools
from tests.conftest import capture_tool


@pytest.fixture
def tool():
    return capture_tool(register_tools, "comfy_workflows")


class TestListSearchDiscover:
    async def test_list(self, tool, isolated_config):
        result = await tool(operation="list")
        assert result["success"] is True
        assert len(result["workflows"]) == 1
        assert result["workflows"][0]["id"] == "test-workflow"

    async def test_search_by_name(self, tool, isolated_config):
        result = await tool(operation="search", query="test")
        assert result["success"] is True
        assert len(result["workflows"]) == 1

    async def test_search_no_match(self, tool, isolated_config):
        result = await tool(operation="search", query="zzzz-nope")
        assert result["workflows"] == []

    async def test_discover(self, tool, isolated_config):
        result = await tool(operation="discover")
        assert result["success"] is True
        assert len(result["sources"]) >= 3
        urls = " ".join(s["url"] for s in result["sources"])
        assert "civitai.com" in urls


class TestGetValidate:
    async def test_get(self, tool, isolated_config):
        result = await tool(operation="get", workflow_id="test-workflow")
        assert result["success"] is True
        wf = result["workflow"]
        assert wf["name"] == "Test Workflow"
        assert wf["model_type"] == "image"
        assert wf["node_count"] >= 3
        assert "Unit fixture" in wf["docs"]

    async def test_get_missing(self, tool, isolated_config):
        result = await tool(operation="get", workflow_id="ghost")
        assert result["success"] is False

    async def test_get_requires_id(self, tool, isolated_config):
        result = await tool(operation="get")
        assert result["success"] is False

    async def test_validate_ok(self, tool, isolated_config):
        result = await tool(operation="validate", workflow_id="test-workflow")
        assert result["success"] is True
        assert result["valid"] is True
        assert result["node_count"] > 0

    async def test_validate_corrupt(self, tool, isolated_config):
        bad = isolated_config["workflows"] / "broken.json"
        bad.write_text("{not-json", encoding="utf-8")
        result = await tool(operation="validate", workflow_id="broken")
        assert result["success"] is False
        assert "Invalid JSON" in result["error"]


class TestRegister:
    async def test_register_and_list(self, tool, isolated_config):
        payload = {
            "_meta": {"name": "Extra"},
            "3": {"class_type": "KSampler", "inputs": {"seed": 0}},
        }
        result = await tool(
            operation="register",
            workflow_id="extra-wf",
            workflow_json=json.dumps(payload),
            name="Extra WF",
            tags="t2i,fast",
            source_url="https://example.com/wf",
        )
        assert result["success"] is True
        assert result["workflow_id"] == "extra-wf"

        listed = await tool(operation="list")
        ids = [w["id"] for w in listed["workflows"]]
        assert "extra-wf" in ids

        got = await tool(operation="get", workflow_id="extra-wf")
        assert got["workflow"]["name"] == "Extra WF"
        assert got["workflow"]["tags"] == "t2i,fast"
        assert got["workflow"]["source_url"] == "https://example.com/wf"

    async def test_register_bad_json(self, tool, isolated_config):
        result = await tool(
            operation="register",
            workflow_id="x",
            workflow_json="{bad",
        )
        assert result["success"] is False

    async def test_register_requires_fields(self, tool, isolated_config):
        result = await tool(operation="register", workflow_id="only-id")
        assert result["success"] is False

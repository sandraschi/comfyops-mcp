"""Tests for comfy_workflows portmanteau tool."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from comfyops_mcp import config as cfg
from comfyops_mcp.tools.workflows import register_tools, _COMMUNITY_SOURCES


@pytest_asyncio.fixture
async def workflow_tool(tmp_workflows_dir):
    """Build a comfy_workflows tool instance with real register_tools."""
    mcp = MagicMock()
    decorated = {}

    def capture_decorator(**kwargs):
        def wrapper(f):
            decorated[f.__name__] = (f, kwargs)
            return f
        return wrapper

    mcp.tool = capture_decorator
    register_tools(mcp)
    fn, _ = decorated.get("comfy_workflows", (None, None))
    assert fn is not None, "comfy_workflows tool not registered"
    return fn


@pytest.fixture
def patch_wf_config(tmp_workflows_dir):
    with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
        yield


class TestWorkflowsList:
    async def test_list_returns_depot(self, workflow_tool, patch_wf_config):
        result = await workflow_tool(operation="list")
        assert result["success"] is True
        assert len(result["workflows"]) >= 1

    async def test_list_empty(self, workflow_tool, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        with patch.object(cfg, "WORKFLOWS_DIR", str(empty)):
            result = await workflow_tool(operation="list")
        assert result["workflows"] == []


class TestWorkflowsGet:
    async def test_get_returns_detail(self, workflow_tool, patch_wf_config):
        result = await workflow_tool(operation="get", workflow_id="test-workflow")
        assert result["success"] is True
        assert result["workflow"]["name"] == "Test Workflow"

    async def test_get_nonexistent(self, workflow_tool, patch_wf_config):
        result = await workflow_tool(operation="get", workflow_id="does-not-exist")
        assert result["success"] is False
        assert "not found" in result["error"]

    async def test_get_without_id(self, workflow_tool):
        result = await workflow_tool(operation="get")
        assert result["success"] is False

    async def test_get_param_details(self, workflow_tool, patch_wf_config):
        result = await workflow_tool(operation="get", workflow_id="test-workflow")
        assert result["workflow"]["model_type"] == "image"


class TestWorkflowsValidate:
    async def test_validate_valid_workflow(self, workflow_tool, patch_wf_config):
        result = await workflow_tool(operation="validate", workflow_id="test-workflow")
        assert result["success"] is True
        assert result["valid"] is True

    async def test_validate_nonexistent(self, workflow_tool):
        result = await workflow_tool(operation="validate", workflow_id="ghost")
        assert result["success"] is False

    async def test_validate_corrupt_json(self, workflow_tool, tmp_workflows_dir):
        bad_file = Path(tmp_workflows_dir) / "broken.json"
        bad_file.write_text("{not valid json")
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(operation="validate", workflow_id="broken")
        assert result["success"] is False
        assert "Invalid JSON" in result["error"]


class TestWorkflowsRegister:
    SAMPLE = json.dumps({
        "_meta": {"name": "New WF", "description": "Fresh from community"},
        "3": {"class_type": "KSampler", "inputs": {"seed": 0}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0]}},
    })

    async def test_register_creates_file(self, workflow_tool, patch_wf_config):
        result = await workflow_tool(
            operation="register", workflow_id="my-wf",
            workflow_json=self.SAMPLE, name="My Workflow",
        )
        assert result["success"] is True
        assert result["workflow_id"] == "my-wf"

    async def test_register_with_tags(self, workflow_tool, patch_wf_config):
        result = await workflow_tool(
            operation="register", workflow_id="tagged-wf",
            workflow_json=self.SAMPLE, tags="t2i,portrait,fast",
        )
        assert result["success"] is True

    async def test_register_missing_params(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(operation="register", workflow_id="x")
        assert result["success"] is False
        assert "workflow_id and workflow_json required" in result["error"]

    async def test_register_invalid_json(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(
                operation="register", workflow_id="bad",
                workflow_json="not json",
            )
        assert result["success"] is False
        assert "Invalid JSON" in result["error"]

    async def test_register_appears_in_list(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            await workflow_tool(
                operation="register", workflow_id="new-one",
                workflow_json=self.SAMPLE,
            )
            result = await workflow_tool(operation="list")
        ids = [w["id"] for w in result["workflows"]]
        assert "new-one" in ids


class TestWorkflowsSearch:
    async def test_search_by_name(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(operation="search", query="Test")
        assert result["success"] is True
        assert len(result["workflows"]) >= 1

    async def test_search_by_id(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(operation="search", query="workflow")
        assert len(result["workflows"]) >= 1

    async def test_search_no_match(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(operation="search", query="zzz_nonexistent_zzz")
        assert result["workflows"] == []

    async def test_search_empty_query(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(operation="search", query="")
        assert len(result["workflows"]) >= 1


class TestWorkflowsDiscover:
    async def test_discover_returns_sources(self, workflow_tool):
        result = await workflow_tool(operation="discover")
        assert result["success"] is True
        assert len(result["sources"]) >= 5

    async def test_discover_includes_key_sources(self, workflow_tool):
        result = await workflow_tool(operation="discover")
        names = [s["name"] for s in result["sources"]]
        assert "ComfyUI Examples" in names
        assert "CivitAI" in names
        assert "ComfyUI Registry" in names

    async def test_discover_sources_have_urls(self, workflow_tool):
        result = await workflow_tool(operation="discover")
        for s in result["sources"]:
            assert s["url"].startswith("http")

    async def test_discover_sources_have_types(self, workflow_tool):
        result = await workflow_tool(operation="discover")
        types = {s["type"] for s in result["sources"]}
        assert "official" in types
        assert "marketplace" in types
        assert "community" in types
        assert "registry" in types


class TestWorkflowsErrorHandling:
    async def test_unknown_operation(self, workflow_tool):
        result = await workflow_tool(operation="destroy")
        assert result["success"] is False
        assert "Unknown operation" in result["error"]

    async def test_get_suggests_alternatives(self, workflow_tool, tmp_workflows_dir):
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(operation="get", workflow_id="nope")
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    async def test_register_suggests_next_steps(self, workflow_tool, tmp_workflows_dir):
        from tests.conftest import SAMPLE_WORKFLOW_JSON
        with patch.object(cfg, "WORKFLOWS_DIR", tmp_workflows_dir):
            result = await workflow_tool(
                operation="register", workflow_id="demo",
                workflow_json=SAMPLE_WORKFLOW_JSON,
            )
        assert "suggestions" in result

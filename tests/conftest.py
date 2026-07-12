"""Shared fixtures for comfyops-mcp tests."""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from comfyops_mcp import config as cfg


# --- Temp directory fixtures ---

@pytest.fixture
def tmp_workflows_dir():
    """Create a temporary workflows directory with a sample workflow."""
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td) / "workflows"
        wf_dir.mkdir(parents=True)
        sample = {
            "_meta": {
                "name": "Test Workflow",
                "description": "A test workflow",
                "model_type": "image",
                "params": {"prompt": "text prompt", "seed": "integer"},
            },
            "3": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 20}},
            "10": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "test.safetensors"}},
            "12": {"class_type": "CLIPTextEncode", "inputs": {"text": "test prompt", "clip": ["10", 1]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["10", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "test", "images": ["8", 0]}},
        }
        (wf_dir / "test-workflow.json").write_text(json.dumps(sample, indent=2))
        (wf_dir / "test-workflow.md").write_text("# Test Workflow\n\nSimple test.", encoding="utf-8")
        yield str(wf_dir)


@pytest.fixture
def tmp_models_dir():
    """Create a temporary models directory with a dummy model file."""
    with tempfile.TemporaryDirectory() as td:
        models_dir = Path(td) / "models"
        models_dir.mkdir(parents=True)
        dummy = models_dir / "flux_test.safetensors"
        dummy.write_bytes(b"x" * (1024 * 1024))
        yield str(models_dir)


@pytest.fixture
def tmp_data_dir():
    """Create a temporary data directory for SQLite library."""
    with tempfile.TemporaryDirectory() as td:
        yield td


# --- Monkey-patch config with temp dirs ---

@pytest.fixture
def patch_config(tmp_workflows_dir, tmp_data_dir):
    """Point config at temp directories for tests that need it."""
    with patch.multiple(
        cfg,
        WORKFLOWS_DIR=tmp_workflows_dir,
        DATA_DIR=tmp_data_dir,
        COMFYUI_URL="http://test-comfyui:11086",
        GENERATION_TIMEOUT=5,
    ):
        yield


@pytest.fixture
def patch_all(tmp_workflows_dir, tmp_data_dir, tmp_models_dir):
    """Point config at temp dirs including models dir."""
    with patch.multiple(
        cfg,
        WORKFLOWS_DIR=tmp_workflows_dir,
        DATA_DIR=tmp_data_dir,
        MODELS_DIR=tmp_models_dir,
        COMFYUI_URL="http://test-comfyui:11086",
        GENERATION_TIMEOUT=5,
    ):
        yield


# --- Mock httpx responses ---

def make_mock_comfyui_health(ok=True, version="0.3.0", vram_free=8 * 1024**3, vram_total=24 * 1024**3):
    """Build a mock ComfyUI /system_stats response."""
    return {
        "system": {
            "comfyui_version": version,
            "devices": [{"name": "NVIDIA RTX 4090", "vram": vram_total}],
            "memory": {"free": vram_free, "total": vram_total},
        }
    }


def make_mock_comfyui_prompt_response(prompt_id="test-prompt-001"):
    """Build a mock ComfyUI /prompt response."""
    return {"prompt_id": prompt_id, "number": 1, "node_errors": {}}


def make_mock_comfyui_history(prompt_id="test-prompt-001", completed=True):
    """Build a mock ComfyUI /history response."""
    return {
        prompt_id: {
            "prompt": {},
            "outputs": {
                "9": {
                    "images": [{"filename": "test_00001_.png", "subfolder": "", "type": "output"}],
                }
            },
            "status": {"completed": completed, "status_str": "success" if completed else "error"},
        }
    }


@pytest_asyncio.fixture
async def mock_httpx_client():
    """Provide a mock httpx.AsyncClient for ComfyUI API calls."""
    client = AsyncMock(spec=httpx.AsyncClient)

    async def mock_get(url, **kwargs):
        if "/system_stats" in url:
            return MagicMock(status_code=200, json=lambda: make_mock_comfyui_health())
        if "/history" in url:
            pid = url.split("/")[-1].split("?")[0]
            return MagicMock(status_code=200, json=lambda pid=pid: make_mock_comfyui_history(pid))
        return MagicMock(status_code=404, text=lambda: "Not found")

    async def mock_post(url, **kwargs):
        if "/prompt" in url:
            return MagicMock(status_code=200, json=make_mock_comfyui_prompt_response)
        return MagicMock(status_code=404, text=lambda: "Not found")

    client.get = mock_get
    client.post = mock_post

    with patch("comfyops_mcp.comfyui_manager._client", client):
        yield client


# --- Sample workflow JSON for tests ---

SAMPLE_WORKFLOW_JSON = json.dumps({
    "_meta": {"name": "Test", "description": "Desc", "model_type": "image"},
    "3": {"class_type": "KSampler", "inputs": {"seed": 0}},
    "10": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "test.safetensors"}},
    "12": {"class_type": "CLIPTextEncode", "inputs": {"text": "test"}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["10", 2]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "test", "images": ["8", 0]}},
})

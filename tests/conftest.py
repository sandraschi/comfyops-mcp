"""Shared fixtures for comfyops-mcp tests — always isolate from live ComfyUI / real data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from comfyops_mcp import config as cfg


@pytest.fixture
def workflows_dir(tmp_path: Path) -> Path:
    wf = tmp_path / "workflows"
    wf.mkdir()
    sample = {
        "_meta": {
            "name": "Test Workflow",
            "description": "A test workflow for unit tests",
            "model_type": "image",
            "params": {"prompt": "text", "seed": "integer"},
            "tags": "t2i,test",
        },
        "3": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 20}},
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "test.safetensors"},
        },
        "12": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "original prompt", "clip": ["10", 1]},
        },
        "13": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "negative", "clip": ["10", 1]},
        },
        "11": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["10", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "test", "images": ["8", 0]},
        },
    }
    (wf / "test-workflow.json").write_text(json.dumps(sample, indent=2), encoding="utf-8")
    (wf / "test-workflow.md").write_text("# Test Workflow\n\nUnit fixture.", encoding="utf-8")
    return wf


@pytest.fixture
def models_dir(tmp_path: Path) -> Path:
    md = tmp_path / "models"
    md.mkdir()
    (md / "flux_test.safetensors").write_bytes(b"x" * (2 * 1024 * 1024))
    (md / "loras").mkdir()
    (md / "loras" / "style.safetensors").write_bytes(b"y" * (512 * 1024))
    return md


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
def isolated_config(workflows_dir: Path, models_dir: Path, data_dir: Path):
    """Point config at temp dirs; never hit live ComfyUI URL without an explicit mock."""
    with patch.multiple(
        cfg,
        WORKFLOWS_DIR=str(workflows_dir),
        MODELS_DIR=str(models_dir),
        DATA_DIR=str(data_dir),
        COMFYUI_URL="http://127.0.0.1:9",
        GENERATION_TIMEOUT=2,
    ):
        yield {
            "workflows": workflows_dir,
            "models": models_dir,
            "data": data_dir,
        }


def capture_tool(register_fn, tool_name: str):
    """Register tools onto a fake MCP and return the named async callable."""
    registered: dict[str, Any] = {}

    class FakeMCP:
        def tool(self, **_kwargs):
            def deco(fn):
                registered[fn.__name__] = fn
                return fn

            return deco

    register_fn(FakeMCP())
    assert tool_name in registered, f"{tool_name} not registered; got {list(registered)}"
    return registered[tool_name]


def mock_response(status_code: int = 200, payload: Any = None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text if text else (json.dumps(payload) if payload is not None else "")
    resp.json = MagicMock(return_value=payload if payload is not None else {})
    return resp


@pytest.fixture
def mock_comfy_client():
    """AsyncClient stand-in; patch get_client so no real network."""
    client = AsyncMock()
    client.get = AsyncMock(
        return_value=mock_response(
            200,
            {
                "system": {
                    "comfyui_version": "0.3.0",
                    "devices": [{"name": "NVIDIA RTX 4090"}],
                    "memory": {"free": 8 * 1024**3, "total": 24 * 1024**3},
                }
            },
        )
    )
    client.post = AsyncMock(return_value=mock_response(200, {"prompt_id": "pid-001", "number": 1, "node_errors": {}}))
    with patch("comfyops_mcp.comfyui_manager.get_client", return_value=client):
        with patch("comfyops_mcp.comfyui_manager._client", client):
            yield client

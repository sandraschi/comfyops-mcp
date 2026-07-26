"""Unit tests for ComfyUI manager (fully mocked — no live sidecar)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from comfyops_mcp import comfyui_manager as mgr
from tests.conftest import mock_response


class TestCheckHealth:
    async def test_ok(self, mock_comfy_client):
        result = await mgr.check_health()
        assert result["ok"] is True
        assert result["comfyui_version"] == "0.3.0"
        assert result["vram_free"] == 8 * 1024**3

    async def test_http_error(self, mock_comfy_client):
        mock_comfy_client.get = AsyncMock(return_value=mock_response(500, text="boom"))
        result = await mgr.check_health()
        assert result["ok"] is False
        assert "500" in result["error"]

    async def test_connect_error(self, mock_comfy_client):
        import httpx

        mock_comfy_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        result = await mgr.check_health()
        assert result["ok"] is False
        assert "not reachable" in result["error"].lower() or "refused" in result["error"].lower()


class TestCheckVram:
    async def test_enough(self, mock_comfy_client):
        result = await mgr.check_vram(4.0)
        assert result["ok"] is True
        assert result["vram_free"] >= 4.0

    async def test_not_enough(self, mock_comfy_client):
        mock_comfy_client.get = AsyncMock(
            return_value=mock_response(
                200,
                {
                    "system": {
                        "comfyui_version": "0.3.0",
                        "devices": [],
                        "memory": {"free": 1 * 1024**3, "total": 24 * 1024**3},
                    }
                },
            )
        )
        result = await mgr.check_vram(8.0)
        assert result["ok"] is False
        assert result["required"] == 8.0

    async def test_offline(self, mock_comfy_client):
        import httpx

        mock_comfy_client.get = AsyncMock(side_effect=httpx.ConnectError("down"))
        result = await mgr.check_vram(4.0)
        assert result["ok"] is False
        assert result["vram_free"] == 0


class TestQueuePrompt:
    async def test_success(self, mock_comfy_client):
        result = await mgr.queue_prompt({"3": {"class_type": "KSampler", "inputs": {}}})
        assert result["ok"] is True
        assert result["prompt_id"] == "pid-001"

    async def test_http_error(self, mock_comfy_client):
        mock_comfy_client.post = AsyncMock(return_value=mock_response(400, text="bad graph"))
        result = await mgr.queue_prompt({})
        assert result["ok"] is False
        assert "400" in result["error"]

    async def test_missing_prompt_id(self, mock_comfy_client):
        mock_comfy_client.post = AsyncMock(return_value=mock_response(200, {"number": 1}))
        result = await mgr.queue_prompt({})
        assert result["ok"] is False
        assert "prompt_id" in result["error"]


class TestWaitForResult:
    async def test_success(self, mock_comfy_client):
        history = {
            "pid-001": {
                "outputs": {"9": {"images": [{"filename": "out.png", "subfolder": "", "type": "output"}]}},
                "status": {"completed": True, "status_str": "success"},
            }
        }
        mock_comfy_client.get = AsyncMock(return_value=mock_response(200, history))
        with patch("comfyops_mcp.comfyui_manager.asyncio.sleep", new_callable=AsyncMock):
            result = await mgr.wait_for_result("pid-001", timeout=5)
        assert result["ok"] is True
        assert result["outputs"][0]["filename"] == "out.png"

    async def test_timeout(self, mock_comfy_client):
        mock_comfy_client.get = AsyncMock(return_value=mock_response(200, {}))
        with patch("comfyops_mcp.comfyui_manager.asyncio.sleep", new_callable=AsyncMock):
            with patch("comfyops_mcp.comfyui_manager.time.time", side_effect=[0, 0.5, 10]):
                result = await mgr.wait_for_result("pid-001", timeout=1)
        assert result["ok"] is False
        assert "Timeout" in result["error"]


class TestListModels:
    async def test_lists_safetensors(self, isolated_config):
        models = await mgr.list_models()
        names = {m["name"] for m in models}
        assert "flux_test" in names
        assert "style" in names
        assert all(m["size_mb"] > 0 for m in models)

    async def test_missing_dir(self, tmp_path, isolated_config):
        with patch.object(mgr._cfg, "MODELS_DIR", str(tmp_path / "nope")):
            assert await mgr.list_models() == []


class TestWorkflowDepot:
    def test_lists_fixture(self, isolated_config):
        depot = mgr.get_workflow_depot()
        assert len(depot) == 1
        assert depot[0]["id"] == "test-workflow"
        assert depot[0]["name"] == "Test Workflow"
        assert "Unit fixture" in depot[0]["docs"]

    def test_empty_dir(self, tmp_path, isolated_config):
        empty = tmp_path / "empty_wf"
        empty.mkdir()
        with patch.object(mgr._cfg, "WORKFLOWS_DIR", str(empty)):
            assert mgr.get_workflow_depot() == []


class TestGatherOutputs:
    def test_extracts_filenames(self):
        outputs = {
            "9": {
                "images": [{"filename": "a.png", "type": "output", "subfolder": ""}],
            },
            "10": {
                "gifs": [{"filename": "b.mp4", "type": "output", "subfolder": "video"}],
            },
        }
        files = mgr._gather_outputs(outputs)
        assert {f["filename"] for f in files} == {"a.png", "b.mp4"}


class TestSidecar:
    def test_start_missing_install(self, tmp_path, isolated_config):
        with patch.object(mgr._cfg, "COMFYUI_DIR", str(tmp_path / "missing")):
            assert mgr.start_sidecar() is None

"""Tests for storage.ArtifactManager - disk URIs, no base64, GC limits."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

from comfyops_mcp.storage import ArtifactManager


class TestEnrich:
    def test_persist_outputs_adds_preview(self, tmp_path: Path):
        mgr = ArtifactManager(output_root=tmp_path)
        img = tmp_path / "panel.png"
        img.write_bytes(b"fake-png")
        out = mgr.persist_outputs([{"filename": "panel.png", "local_path": str(img)}])
        assert out[0]["file_uri"].endswith("panel.png")
        assert out[0]["markdown_preview"].startswith("![Panel](")


class TestPersistComfyImage:
    async def test_downloads_and_saves(self, tmp_path: Path, isolated_config):
        mgr = ArtifactManager(output_root=tmp_path)
        fake_bytes = b"\x89PNG fake"
        from unittest.mock import MagicMock

        resp = AsyncMock()
        resp.content = fake_bytes
        resp.raise_for_status = MagicMock()
        client = AsyncMock()
        client.__aenter__.return_value.get = AsyncMock(return_value=resp)
        with patch("comfyops_mcp.storage.httpx.AsyncClient", return_value=client):
            saved = await mgr.persist_comfy_image("out_0001.png", "", "output")
        assert saved.exists()
        assert saved.read_bytes() == fake_bytes

    async def test_gc_caps_file_count(self, tmp_path: Path):
        import comfyops_mcp.storage as store_mod

        mgr = ArtifactManager(output_root=tmp_path)
        for i in range(5):
            (tmp_path / f"f{i}.png").write_bytes(b"x")
        with patch.object(store_mod, "MAX_ARTIFACT_FILES", 3):
            mgr._enforce_limits()
        remaining = list(tmp_path.glob("*.png"))
        assert len(remaining) == 3

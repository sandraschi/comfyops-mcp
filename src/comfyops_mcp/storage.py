"""Disk artifact manager - Drive 2026-11-03 spec.

Zero base64 in JSON-RPC: persist ComfyUI outputs to artifacts/,
return file URIs + Markdown previews. Rolling cache prevents disk exhaustion.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from comfyops_mcp import config as _cfg

logger = logging.getLogger(__name__)

MAX_ARTIFACT_FILES = 200
MAX_ARTIFACT_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB


class ArtifactManager:
    def __init__(self, output_root: Path | str | None = None):
        base = Path(output_root) if output_root else Path(_cfg.DATA_DIR) / "artifacts" / "comics"
        self.output_root = base
        self.output_root.mkdir(parents=True, exist_ok=True)

    async def persist_comfy_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Path:
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.get(f"{_cfg.COMFYUI_URL}/view", params=params)
            res.raise_for_status()
        target = self.output_root / Path(filename).name
        # Avoid collision
        counter = 1
        while target.exists():
            target = self.output_root / f"{Path(filename).stem}_{counter}{Path(filename).suffix}"
            counter += 1
        target.write_bytes(res.content)
        self._enforce_limits()
        return target.resolve()

    def persist_outputs(self, outputs: list[dict]) -> list[dict]:
        """Attach file_uri + markdown preview to already-downloaded entries (sync helper)."""
        enriched = []
        for item in outputs:
            path = item.get("local_path") or item.get("filename", "")
            uri = Path(path).as_uri() if path and Path(path).is_absolute() else path
            enriched.append(
                {
                    **item,
                    "file_uri": uri,
                    "markdown_preview": f"![Panel]({uri})" if uri else "",
                }
            )
        return enriched

    def _enforce_limits(self) -> None:
        try:
            files = sorted(
                (p for p in self.output_root.iterdir() if p.is_file()),
                key=lambda p: p.stat().st_mtime,
            )
            total = sum(p.stat().st_size for p in files)
            while (len(files) > MAX_ARTIFACT_FILES or total > MAX_ARTIFACT_BYTES) and files:
                oldest = files.pop(0)
                total -= oldest.stat().st_size
                oldest.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Artifact GC failed: %s", exc)

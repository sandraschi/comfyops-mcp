"""Async WebSocket telemetry for ComfyUI - Drive 2026-11-03 modernized spec.

Replaces blocking poll loops with /ws event streaming. Falls back to
/history polling when websockets lib or WS endpoint is unavailable.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from comfyops_mcp import config as _cfg

logger = logging.getLogger(__name__)


class ComfyAsyncClient:
    """Minimal async client: queue prompt, stream /ws progress to completion."""

    def __init__(self, base_url: str | None = None):
        base = (base_url or _cfg.COMFYUI_URL).rstrip("/")
        self.base_url = base
        self.ws_url = base.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
        self.client_id = str(uuid.uuid4())

    async def queue_and_stream(self, workflow_graph: dict[str, Any]) -> AsyncGenerator[dict[str, Any], None]:
        """Yield progress/completed/error events. Requires `websockets` package."""
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError("websockets package not installed") from exc

        async with websockets.connect(f"{self.ws_url}?clientId={self.client_id}") as ws:
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    f"{self.base_url}/prompt",
                    json={"prompt": workflow_graph, "client_id": self.client_id},
                )
                res.raise_for_status()
                prompt_id = res.json()["prompt_id"]

            while True:
                raw = await ws.recv()
                if not isinstance(raw, str):
                    continue
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                msg_type = event.get("type")
                data = event.get("data", {})
                if msg_type == "progress":
                    yield {"status": "progress", "value": data.get("value"), "max": data.get("max")}
                elif msg_type == "executed" and data.get("prompt_id") == prompt_id:
                    if "output" in data:
                        yield {"status": "completed", "output": data["output"], "prompt_id": prompt_id}
                        break
                elif msg_type == "execution_error" and data.get("prompt_id") == prompt_id:
                    yield {"status": "error", "error": data, "prompt_id": prompt_id}
                    break
                elif msg_type == "execution_interrupted" and data.get("prompt_id") == prompt_id:
                    yield {"status": "error", "error": "interrupted", "prompt_id": prompt_id}
                    break


async def stream_to_completion(workflow_graph: dict[str, Any], timeout: int | None = None) -> dict[str, Any]:
    """Run queue_and_stream to terminal event. Returns {ok, outputs|error}."""
    import asyncio

    actual_timeout = timeout if timeout is not None else _cfg.GENERATION_TIMEOUT
    client = ComfyAsyncClient()

    async def _run() -> dict[str, Any]:
        from comfyops_mcp.comfyui_manager import _gather_outputs, free_vram

        async for event in client.queue_and_stream(workflow_graph):
            if event["status"] == "completed":
                outputs = event.get("output", {})
                # /ws executed output shape differs from /history; normalize via _gather
                await free_vram()
                return {
                    "ok": True,
                    "outputs": _gather_outputs(outputs) if isinstance(outputs, dict) else [],
                    "prompt_id": event.get("prompt_id", ""),
                }
            if event["status"] == "error":
                return {"ok": False, "error": str(event.get("error")), "prompt_id": event.get("prompt_id", "")}
        return {"ok": False, "error": "WS stream ended without terminal event"}

    try:
        return await asyncio.wait_for(_run(), timeout=actual_timeout)
    except TimeoutError:
        return {"ok": False, "error": f"WS timeout after {actual_timeout}s"}

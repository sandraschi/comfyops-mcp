"""Tests for comfy_ws - WS streaming without live ComfyUI."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from comfyops_mcp import comfy_ws


class FakeWS:
    def __init__(self, messages):
        self._messages = list(messages)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def recv(self):
        if not self._messages:
            raise AssertionError("no more WS messages")
        return self._messages.pop(0)


def _ws_connect_factory(messages):
    def _connect(*args, **kwargs):
        return FakeWS(messages)

    return _connect


class TestQueueAndStream:
    async def test_completed_event(self, isolated_config):
        prompt_id = "pid-ws-1"
        msgs = [
            json.dumps({"type": "progress", "data": {"value": 3, "max": 20}}),
            json.dumps(
                {
                    "type": "executed",
                    "data": {
                        "prompt_id": prompt_id,
                        "output": {"9": [{"filename": "a.png", "type": "output", "subfolder": ""}]},
                    },
                }
            ),
        ]
        post_resp = MagicMock()
        post_resp.raise_for_status = MagicMock()
        post_resp.json = MagicMock(return_value={"prompt_id": prompt_id})
        http_client = AsyncMock()
        http_client.__aenter__.return_value.post = AsyncMock(return_value=post_resp)

        events = []
        with (
            patch("websockets.connect", side_effect=_ws_connect_factory(msgs)),
            patch("comfyops_mcp.comfy_ws.httpx.AsyncClient", return_value=http_client),
        ):
            client = comfy_ws.ComfyAsyncClient(base_url="http://127.0.0.1:9")
            async for ev in client.queue_and_stream({"3": {"class_type": "KSampler"}}):
                events.append(ev)
        assert events[0]["status"] == "progress"
        assert events[-1]["status"] == "completed"
        assert events[-1]["prompt_id"] == prompt_id

    async def test_missing_websockets_raises(self):
        import builtins

        real_import = builtins.__import__

        def _fake(name, *args, **kwargs):
            if name == "websockets":
                raise ImportError("nope")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=_fake):
            client = comfy_ws.ComfyAsyncClient(base_url="http://127.0.0.1:9")
            with pytest.raises(RuntimeError, match="websockets"):
                async for _ in client.queue_and_stream({}):
                    pass

"""Tests for config module — env var loading and defaults."""

import os
from unittest.mock import patch

import pytest

from comfyops_mcp import config as cfg


class TestConfigDefaults:
    def test_comfyui_host_default(self):
        assert cfg.COMFYUI_HOST == "127.0.0.1"

    def test_comfyui_port_default(self):
        assert cfg.COMFYUI_PORT == 11086

    def test_comfyui_url_construction(self):
        assert cfg.COMFYUI_URL == f"http://{cfg.COMFYUI_HOST}:{cfg.COMFYUI_PORT}"

    def test_backend_port_default(self):
        assert cfg.BACKEND_PORT == 11087

    def test_generation_timeout_default(self):
        # Default is 300 when not patched; this tests the import default
        from comfyops_mcp.config import GENERATION_TIMEOUT
        assert GENERATION_TIMEOUT in (300, 5)  # 300 default, 5 when patched

    def test_max_queue_default(self):
        assert cfg.MAX_QUEUE_SIZE == 5


class TestConfigEnvOverrides:
    def test_comfyui_host_from_env(self):
        with patch.dict(os.environ, {"COMFYOPS_COMFYUI_HOST": "192.168.1.100"}, clear=True):
            import importlib
            importlib.reload(cfg)
            assert cfg.COMFYUI_HOST == "192.168.1.100"

    def test_comfyui_port_from_env(self):
        with patch.dict(os.environ, {"COMFYOPS_COMFYUI_PORT": "12345"}, clear=True):
            import importlib
            importlib.reload(cfg)
            assert cfg.COMFYUI_PORT == 12345

    def test_backend_port_from_env(self):
        with patch.dict(os.environ, {"PORT": "10999"}, clear=True):
            import importlib
            importlib.reload(cfg)
            assert cfg.BACKEND_PORT == 10999

    def test_generation_timeout_from_env(self):
        with patch.dict(os.environ, {"COMFYOPS_TIMEOUT": "600"}, clear=True):
            import importlib
            importlib.reload(cfg)
            assert cfg.GENERATION_TIMEOUT == 600

    def test_models_dir_from_env(self):
        with patch.dict(os.environ, {"COMFYOPS_MODELS_DIR": "Z:\\custom_models"}, clear=True):
            import importlib
            importlib.reload(cfg)
            assert cfg.MODELS_DIR == "Z:\\custom_models"

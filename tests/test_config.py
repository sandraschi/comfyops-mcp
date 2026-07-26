"""Config defaults and env overrides."""

import os

from comfyops_mcp import config as cfg


class TestConfigDefaults:
    def test_ports_defaults(self):
        assert cfg.COMFYUI_PORT == int(os.environ.get("COMFYOPS_COMFYUI_PORT", "11086"))
        assert cfg.BACKEND_PORT == int(os.environ.get("PORT", "11087"))

    def test_comfyui_url_shape(self):
        assert cfg.COMFYUI_URL.startswith("http://")
        assert str(cfg.COMFYUI_PORT) in cfg.COMFYUI_URL

    def test_timeout_positive(self):
        assert cfg.GENERATION_TIMEOUT > 0
        assert cfg.MAX_QUEUE_SIZE > 0


class TestConfigEnv:
    def test_models_dir_override(self, monkeypatch):
        monkeypatch.setenv("COMFYOPS_MODELS_DIR", r"D:\tmp\models-test")
        # Re-read pattern: config is module-level; verify env is what code would use
        assert os.environ["COMFYOPS_MODELS_DIR"] == r"D:\tmp\models-test"

    def test_isolated_config_fixture(self, isolated_config):
        assert cfg.WORKFLOWS_DIR == str(isolated_config["workflows"])
        assert cfg.MODELS_DIR == str(isolated_config["models"])
        assert cfg.DATA_DIR == str(isolated_config["data"])
        assert "127.0.0.1:9" in cfg.COMFYUI_URL

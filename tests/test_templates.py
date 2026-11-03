"""Tests for templates.TemplateEngine - Drive 2026-11-03 declarative patching."""

from __future__ import annotations

import json

from comfyops_mcp.templates import STYLE_PRESETS, TemplateEngine


def _write_template(workflows_dir, name="flux_dev_panel"):
    graph = {
        "_meta": {"name": name},
        "12": {
            "class_type": "CLIPTextEncodeFlux",
            "inputs": {"clip_l": "old", "t5xxl": "old", "clip": ["11", 0]},
        },
        "16": {"class_type": "KSampler", "inputs": {"seed": 0, "steps": 20}},
        "15": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 512, "height": 512}},
    }
    (workflows_dir / f"{name}.json").write_text(json.dumps(graph), encoding="utf-8")


class TestTemplateEngine:
    def test_available(self, isolated_config):
        _write_template(isolated_config["workflows"])
        engine = TemplateEngine(isolated_config["workflows"])
        assert "flux_dev_panel" in engine.available()

    def test_patch_prompt_seed_size(self, isolated_config):
        _write_template(isolated_config["workflows"])
        engine = TemplateEngine(isolated_config["workflows"])
        graph = engine.load_and_patch(
            "flux_dev_panel",
            {"positive_prompt": "explorer finds idol", "seed": 7, "width": 1024, "height": 1024},
        )
        assert graph["12"]["inputs"]["clip_l"] == "explorer finds idol"
        assert graph["12"]["inputs"]["t5xxl"] == "explorer finds idol"
        assert graph["16"]["inputs"]["seed"] == 7
        assert graph["15"]["inputs"]["width"] == 1024

    def test_style_preset_injected(self, isolated_config):
        _write_template(isolated_config["workflows"])
        engine = TemplateEngine(isolated_config["workflows"])
        graph = engine.load_and_patch(
            "flux_dev_panel",
            {"positive_prompt": "a hero shouts", "style_preset": "vintage_pulp"},
        )
        assert graph["12"]["inputs"]["clip_l"].startswith(STYLE_PRESETS["vintage_pulp"])

    def test_missing_template_raises(self, isolated_config):
        engine = TemplateEngine(isolated_config["workflows"])
        try:
            engine.load_and_patch("ghost", {})
            raise AssertionError("should raise")
        except FileNotFoundError:
            pass

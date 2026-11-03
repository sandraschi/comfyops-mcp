"""Declarative workflow template engine - Drive 2026-11-03 spec.

Loads canonical API-format JSON templates from workflows/ and patches
nodes by class_type + _meta.title. Replaces ad-hoc per-tool patch loops.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STYLE_PRESETS = {
    "vintage_pulp": (
        "Vintage 1930s adventure comic, George McManus ink work, bold expressive contours, subtle newsprint texture. "
    ),
    "modern_graphic_novel": (
        "Contemporary high-contrast indie graphic novel, brush ink outlines, dynamic spot blacks. "
    ),
    "ligne_claire": (
        "Classic Franco-Belgian ligne claire style, clean geometric lines, uniform line weight, flat primary colors. "
    ),
}


class TemplateEngine:
    def __init__(self, workflow_dir: Path | str):
        self.workflow_dir = Path(workflow_dir)

    def available(self) -> list[str]:
        if not self.workflow_dir.exists():
            return []
        return sorted(p.stem for p in self.workflow_dir.glob("*.json"))

    def load_and_patch(self, template_name: str, overrides: dict[str, Any]) -> dict[str, Any]:
        path = self.workflow_dir / f"{template_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Workflow template {template_name} not found at {path}")
        graph = json.loads(path.read_text(encoding="utf-8"))

        # Style preset injection
        style = overrides.get("style_preset")
        if style and style in STYLE_PRESETS and "positive_prompt" in overrides:
            overrides = dict(overrides)
            overrides["positive_prompt"] = STYLE_PRESETS[style] + overrides["positive_prompt"]

        positive = overrides.get("positive_prompt")
        negative = overrides.get("negative_prompt")
        seed = overrides.get("seed")
        steps = overrides.get("steps")
        cfg = overrides.get("cfg")
        width = overrides.get("width")
        height = overrides.get("height")
        clip_seen = 0

        for node_id, node in graph.items():
            if not isinstance(node, dict) or node_id.startswith("_"):
                continue
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if class_type in ("CLIPTextEncode", "CLIPTextEncodeFlux", "TextEncodeQwenImageEdit"):
                if any(k in inputs for k in ("text", "clip_l", "t5xxl", "prompt")):
                    clip_seen += 1
                    text = positive if clip_seen == 1 else (negative or "")
                    if text is None:
                        continue
                    for k in ("text", "clip_l", "t5xxl", "prompt"):
                        if k in inputs:
                            inputs[k] = text
            elif class_type in ("KSampler", "KSamplerAdvanced", "SamplerCustom"):
                if seed is not None and "seed" in inputs:
                    inputs["seed"] = seed
                if steps is not None and "steps" in inputs:
                    inputs["steps"] = steps
                if cfg is not None and "cfg" in inputs:
                    inputs["cfg"] = cfg
            elif class_type in ("EmptyLatentImage", "EmptySD3LatentImage", "EmptyFlux2LatentImage"):
                if width is not None:
                    inputs["width"] = width
                if height is not None:
                    inputs["height"] = height
            elif class_type == "RandomNoise" and seed is not None and "noise_seed" in inputs:
                inputs["noise_seed"] = seed

        return graph

"""comfy_comic portmanteau - Drive 2026-11-03 panel-by-panel + strip assembler.

Two-pass hybrid: pass 1 generates art (empty or short-text balloon),
pass 2 is deterministic (PIL/SVG overlay done by caller or future tool).
Strip assembler is pure PIL, no GPU needed.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP
from PIL import Image, ImageOps

from comfyops_mcp import config as _cfg
from comfyops_mcp.comfyui_manager import check_vram, ensure_comfyui_running, queue_prompt
from comfyops_mcp.storage import ArtifactManager
from comfyops_mcp.templates import STYLE_PRESETS, TemplateEngine
from comfyops_mcp.tools.library import record_generation

logger = logging.getLogger(__name__)

_VRAM_MAP = {"flux_dev_panel": 12.0, "flux_clean_balloon": 12.0}


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": False})
    async def comfy_comic(
        operation: Annotated[Literal["generate_panel", "assemble_strip"], "Comic operation."],
        prompt: Annotated[str | None, "Scene prompt (no dialogue) for generate_panel."] = None,
        verbatim_dialogue: Annotated[str | None, "Short exact dialogue <=12 words for T5 (optional)."] = None,
        style_preset: Annotated[
            Literal["vintage_pulp", "modern_graphic_novel", "ligne_claire"],
            "Public-domain style homage.",
        ] = "vintage_pulp",
        template: Annotated[str, "Template: flux_dev_panel or flux_clean_balloon."] = "flux_dev_panel",
        width: Annotated[int, "Panel width."] = 1024,
        height: Annotated[int, "Panel height."] = 1024,
        seed: Annotated[int | None, "Seed. Omit for random."] = None,
        panel_paths: Annotated[list[str] | None, "Local image paths for assemble_strip."] = None,
        layout: Annotated[Literal["horizontal_strip", "grid_2x2"], "Strip layout."] = "horizontal_strip",
        gutter_width: Annotated[int, "Gutter px."] = 24,
    ) -> dict:
        """Panel-by-panel comic generation + strip assembly.

        ## Return Format
        generate_panel: {success, panel_path, markdown_preview, seed_used}
        assemble_strip: {success, strip_path, dimensions}

        ## Examples
            comfy_comic(operation="generate_panel", prompt="explorer finds idol in cavern",
                        verbatim_dialogue="STOP!", style_preset="vintage_pulp")
            comfy_comic(operation="assemble_strip", panel_paths=["a.png","b.png","c.png"])
        """
        if operation == "assemble_strip":
            return _assemble(panel_paths or [], layout, gutter_width)

        # generate_panel
        if not prompt:
            return {"success": False, "error": "prompt required for generate_panel."}
        if verbatim_dialogue and len(verbatim_dialogue.split()) > 12:
            logger.warning("Long dialogue (%d words) risks T5 drift", len(verbatim_dialogue.split()))

        boot = await ensure_comfyui_running()
        if not boot.get("ok"):
            return {"success": False, "error": boot.get("error", "ComfyUI unavailable")}

        vram = await check_vram(_VRAM_MAP.get(template, 12.0))
        if not vram["ok"]:
            return {"success": False, "error": vram["error"], "error_type": "vram"}

        engine = TemplateEngine(Path(_cfg.WORKFLOWS_DIR))
        seed_val = seed if seed is not None else random.randint(0, 2**32 - 1)
        full_prompt = (STYLE_PRESETS.get(style_preset, "") + prompt).strip()
        if verbatim_dialogue and template == "flux_dev_panel":
            full_prompt += f' A speech balloon containing the text: "{verbatim_dialogue}"'

        try:
            graph = engine.load_and_patch(
                template,
                {
                    "positive_prompt": full_prompt,
                    "seed": seed_val,
                    "width": width,
                    "height": height,
                    "style_preset": None,  # already injected
                },
            )
        except FileNotFoundError as exc:
            return {"success": False, "error": str(exc)}

        # WS-first, poll fallback
        outputs: list[dict] = []
        prompt_id = ""
        try:
            from comfyops_mcp.comfy_ws import stream_to_completion

            ws_res = await stream_to_completion({k: v for k, v in graph.items() if not k.startswith("_")})
            if ws_res.get("ok"):
                outputs = ws_res.get("outputs", [])
                prompt_id = ws_res.get("prompt_id", "")
        except Exception as exc:  # websockets missing or WS down
            logger.info("WS path failed (%s), falling back to poll", exc)

        if not outputs:
            from comfyops_mcp.comfyui_manager import wait_for_result
            from comfyops_mcp.workflow_utils import normalize_for_prompt

            api_wf = normalize_for_prompt(graph)
            q = await queue_prompt(api_wf)
            if not q["ok"]:
                return {"success": False, "error": q["error"]}
            prompt_id = q["prompt_id"]
            gen = await wait_for_result(prompt_id, _cfg.GENERATION_TIMEOUT)
            if not gen["ok"]:
                return {"success": False, "error": gen["error"], "prompt_id": prompt_id}
            outputs = gen.get("outputs", [])

        # Persist to disk artifacts, return URIs (zero base64)
        storage = ArtifactManager()
        saved: list[str] = []
        for item in outputs:
            try:
                p = await storage.persist_comfy_image(
                    item.get("filename", ""), item.get("subfolder", ""), item.get("type", "output")
                )
                saved.append(str(p))
            except Exception as exc:
                logger.warning("persist failed for %s: %s", item, exc)

        if not saved:
            # ComfyUI local output fallback: filenames only
            return {
                "success": True,
                "prompt_id": prompt_id,
                "panel_path": "",
                "outputs": outputs,
                "seed_used": seed_val,
                "message": "Generated but artifact download failed; see outputs filenames.",
            }

        record_generation(
            prompt_id=prompt_id or "ws",
            workflow_id=template,
            prompt_text=full_prompt,
            seed=seed_val,
            model=template,
            outputs=[{"filename": s} for s in saved],
        )
        uri = Path(saved[0]).as_uri()
        return {
            "success": True,
            "panel_path": saved[0],
            "markdown_preview": f"![Panel]({uri})",
            "seed_used": seed_val,
            "message": f"Panel saved with seed {seed_val}.",
        }


def _assemble(panel_paths: list[str], layout: str, gutter: int) -> dict:
    if not panel_paths:
        return {"success": False, "error": "panel_paths required."}
    try:
        loaded = [Image.open(p).convert("RGB") for p in panel_paths]
    except Exception as exc:
        return {"success": False, "error": f"Cannot open panels: {exc}"}

    if layout == "grid_2x2" and len(loaded) != 4:
        return {"success": False, "error": "grid_2x2 requires exactly 4 panels."}

    border = 4
    if layout == "horizontal_strip":
        total_w = sum(im.width for im in loaded) + gutter * (len(loaded) + 1)
        max_h = max(im.height for im in loaded) + gutter * 2
        strip = Image.new("RGB", (total_w, max_h), color="#FFFFFF")
        x = gutter
        for im in loaded:
            bordered = ImageOps.expand(im, border=border, fill="#000000")
            strip.paste(bordered, (x, gutter))
            x += bordered.width + gutter
    else:
        pw = max(im.width for im in loaded)
        ph = max(im.height for im in loaded)
        total_w = pw * 2 + gutter * 3
        total_h = ph * 2 + gutter * 3
        strip = Image.new("RGB", (total_w, total_h), color="#FFFFFF")
        positions = [
            (gutter, gutter),
            (pw + gutter * 2, gutter),
            (gutter, ph + gutter * 2),
            (pw + gutter * 2, ph + gutter * 2),
        ]
        for im, pos in zip(loaded, positions, strict=True):
            strip.paste(ImageOps.expand(im, border=border, fill="#000000"), pos)

    out_dir = Path(_cfg.DATA_DIR) / "artifacts" / "comics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "final_assembled_strip.png"
    strip.save(out_file, format="PNG")
    return {
        "success": True,
        "strip_path": str(out_file.resolve()),
        "dimensions": [strip.width, strip.height],
        "message": f"Assembled {len(loaded)} panels ({layout}).",
    }

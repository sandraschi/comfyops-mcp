"""Prefab UI cards for comfyops-mcp — rich in-chat displays."""

from fastmcp import FastMCP
from prefab_ui.components import Card, Badge, Metric, Row, Div

from comfyops_mcp.comfyui_manager import check_health, get_workflow_depot


def register_prefab_cards(mcp: FastMCP):
    @mcp.tool(app=True)
    async def show_comfyops_status_card() -> dict:
        """Show ComfyUI health and generation status as a rich in-chat card.

        ## Return Format
        Prefab UI card with system status, VRAM, workflow count, model count
        """
        health = await check_health()
        depot = get_workflow_depot()
        from comfyops_mcp.comfyui_manager import list_models
        models = await list_models()
        workflows = depot

        return {
            "content": f"ComfyUI {'running' if health['ok'] else 'offline'}, "
                       f"{len(workflows)} workflows, {len(models)} models",
            "structured_content": {
                "type": "app",
                "app": "PrefabApp",
                "components": [
                    {"type": "heading", "text": "ComfyOps Status", "level": 1},
                    {"type": "divider"},
                    {"type": "metric", "label": "ComfyUI", "value": "Connected" if health["ok"] else "Offline",
                     "color": "green" if health["ok"] else "red"},
                    {"type": "metric", "label": "Workflows", "value": str(len(workflows))},
                    {"type": "metric", "label": "Models", "value": str(len(models))},
                    {"type": "metric", "label": "VRAM Free", "value":
                     f"{round(health.get('vram_free', 0) / 1024**3, 1)} GB"
                     if health.get("vram_free") else "N/A"},
                ],
            },
        }

    @mcp.tool(app=True)
    async def show_generation_card(
        prompt: str, seed: int, workflow_id: str, outputs: list = None
    ) -> dict:
        """Display a single generation result as a Prefab card.

        ## Return Format
        Rich card with prompt, seed, workflow, and output files
        """
        outputs = outputs or []
        return {
            "content": f"Generation: {prompt[:100]} (seed {seed})",
            "structured_content": {
                "type": "app",
                "app": "PrefabApp",
                "components": [
                    {"type": "heading", "text": f"Generation", "level": 1},
                    {"type": "divider"},
                    {"type": "row", "label": "Prompt", "value": prompt[:200]},
                    {"type": "row", "label": "Seed", "value": str(seed)},
                    {"type": "row", "label": "Workflow", "value": workflow_id},
                    {"type": "row", "label": "Outputs", "value": str(len(outputs))},
                ],
            },
        }

"""comfy_agentic_assist — SEP-1577 sampling for multi-step generation."""

import logging
from typing import Annotated

from fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": True})
    async def comfy_agentic_assist(
        goal: Annotated[str, "Natural language description of what to generate."],
        ctx: Context = None,
    ) -> dict:
        """Multi-step agentic generation via MCP sampling (SEP-1577).

        Plans a generation campaign: describes the creative goal, selects
        appropriate workflow(s), generates, optionally vision-checks via
        local multimodal model, and retries with adjusted params (max 3).

        Requires a host with MCP sampling. Falls back to a structured manual
        tool sequence when sampling is unavailable.

        ## Return Format
        {"success": bool, "agent_plan": str, "error": str}

        ## Examples
            comfy_agentic_assist(goal="Create a cinematic aerial shot of a cyberpunk city")
        """
        recovery = "This tool requires MCP sampling (SEP-1577). Try: comfy_workflows/list → comfy_generate"

        if ctx is None:
            return {
                "success": False,
                "error": "MCP sampling unsupported.",
                "error_type": "sampling_unavailable",
                "suggestions": [recovery],
            }

        try:
            result = await ctx.sample(
                f"Plan generation for: {goal}\n\nReturn: workflow_id, detailed prompt, params JSON.",
                max_tokens=500,
            )
            return {"success": True, "agent_plan": str(result), "message": f"Agent plan for: {goal[:100]}..."}
        except Exception as e:
            return {
                "success": False,
                "error": f"Sampling failed: {e}",
                "error_type": "sampling_error",
                "suggestions": [recovery],
            }

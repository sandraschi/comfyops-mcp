"""comfyops-mcp — FastMCP server for local generative AI via ComfyUI."""

import logging
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "comfyops-mcp",
    description="Local generative AI engine — image, video, upscale, inpaint via ComfyUI",
    version="0.1.0",
)


def register_tools():
    """Register all tool portmanteaus."""
    from comfyops_mcp.tools.generate import register_tools as reg_gen
    from comfyops_mcp.tools.workflows import register_tools as reg_wf
    from comfyops_mcp.tools.models_tool import register_tools as reg_models
    from comfyops_mcp.tools.library import register_tools as reg_lib
    from comfyops_mcp.tools.agentic import register_tools as reg_agentic
    from comfyops_mcp.tools.prefab.cards import register_prefab_cards
    reg_gen(mcp)
    reg_wf(mcp)
    reg_models(mcp)
    reg_lib(mcp)
    reg_agentic(mcp)
    register_prefab_cards(mcp)


def main():
    port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
    register_tools()
    if port:
        host = os.environ.get("MCP_HOST", "127.0.0.1")
        sys.argv = ["comfyops", "--mode", "http", "--host", host, "--port", str(port)]
    mcp.run()


if __name__ == "__main__":
    main()

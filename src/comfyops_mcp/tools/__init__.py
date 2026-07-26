"""Tool registrations — portmanteau re-exports for FastMCP import-time registration."""
from comfyops_mcp.tools.agentic import register_tools as register_agentic
from comfyops_mcp.tools.generate import register_tools as register_generate
from comfyops_mcp.tools.library import register_tools as register_library
from comfyops_mcp.tools.models_tool import register_tools as register_models
from comfyops_mcp.tools.prefab.cards import register_prefab_cards
from comfyops_mcp.tools.workflows import register_tools as register_workflows

__all__ = [
    "register_agentic",
    "register_generate",
    "register_library",
    "register_models",
    "register_prefab_cards",
    "register_workflows",
]

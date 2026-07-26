"""Server registration and CORS smoke checks."""

from __future__ import annotations

from comfyops_mcp.server import mcp


def test_register_tools_exposes_portmanteaus():
    names: list[str] = []

    class FakeMCP:
        def tool(self, **_kwargs):
            def deco(fn):
                names.append(fn.__name__)
                return fn

            return deco

    fake = FakeMCP()
    from comfyops_mcp.tools.agentic import register_tools as reg_agentic
    from comfyops_mcp.tools.generate import register_tools as reg_gen
    from comfyops_mcp.tools.library import register_tools as reg_lib
    from comfyops_mcp.tools.models_tool import register_tools as reg_models
    from comfyops_mcp.tools.workflows import register_tools as reg_wf

    reg_gen(fake)
    reg_wf(fake)
    reg_models(fake)
    reg_lib(fake)
    reg_agentic(fake)

    assert "comfy_generate" in names
    assert "comfy_workflows" in names
    assert "comfy_models" in names
    assert "comfy_library" in names
    assert "comfy_agentic_assist" in names


def test_cors_allows_dashboard_port():
    import inspect

    from comfyops_mcp import server as srv

    src = inspect.getsource(srv._run_http)
    assert "11088" in src
    assert "CORSMiddleware" in src


def test_mcp_app_name():
    assert mcp.name == "comfyops-mcp"

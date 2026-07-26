"""comfyops-mcp — FastMCP server for local generative AI via ComfyUI."""

import logging
import os
import time as _time

from fastmcp import FastMCP

from comfyops_mcp.comfyui_manager import check_health as _check_comfyui_health

logger = logging.getLogger(__name__)

_START_TIME = _time.time()

mcp = FastMCP(
    "comfyops-mcp",
    instructions="Local generative AI engine — image, video, upscale, inpaint via ComfyUI",
    version="0.1.0",
)


def _error_response(error: str, error_type: str = "general", **kwargs) -> dict:
    logger.exception("Tool error: %s [%s]", error, error_type)
    return {"success": False, "error": error, "error_type": error_type, **kwargs}


def register_tools():
    from comfyops_mcp.tools.agentic import register_tools as reg_agentic
    from comfyops_mcp.tools.generate import register_tools as reg_gen
    from comfyops_mcp.tools.library import register_tools as reg_lib
    from comfyops_mcp.tools.models_tool import register_tools as reg_models
    from comfyops_mcp.tools.prefab.cards import register_prefab_cards
    from comfyops_mcp.tools.workflows import register_tools as reg_wf
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
        _run_http(port)
    else:
        mcp.run()


def _run_http(port: int):
    import uvicorn
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    host = os.environ.get("MCP_HOST", "127.0.0.1")
    tool_count = len(mcp._tool_manager.tools) if hasattr(mcp, "_tool_manager") else 0

    async def health(request: Request) -> JSONResponse:
        comfy = await _check_comfyui_health()
        return JSONResponse({
            "status": "ok",
            "server": "comfyops-mcp",
            "version": "0.1.0",
            "uptime_seconds": int(_time.time() - _START_TIME),
            "tool_count": tool_count,
            "providers": {"comfyui": comfy},
        })

    async def diagnostics(request: Request) -> JSONResponse:
        await _check_comfyui_health()
        tool_names = []
        if hasattr(mcp, "_tool_manager"):
            tool_names = [{"name": name} for name in mcp._tool_manager.tools]
        return JSONResponse({
            "status": "ok",
            "server": "comfyops-mcp",
            "version": "0.1.0",
            "uptime_seconds": int(_time.time() - _START_TIME),
            "tool_count": len(tool_names),
            "tools": tool_names,
            "system": {"windows": True},
            "errors": [],
        })

    app = Starlette(
        routes=[
            Route("/api/health", endpoint=health),
            Route("/api/v1/diagnostics", endpoint=diagnostics),
            Route("/health", endpoint=health),
            Mount("/", app=mcp.sse_app()),
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=[
                    f"http://127.0.0.1:{port}",
                    f"http://localhost:{port}",
                    "http://127.0.0.1:11088",
                    "http://localhost:11088",
                    "http://tauri.localhost",
                    "https://tauri.localhost",
                    "tauri://localhost",
                ],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        ],
    )

    uvicorn.run(app, host=host, port=int(port), log_level="info")


if __name__ == "__main__":
    main()

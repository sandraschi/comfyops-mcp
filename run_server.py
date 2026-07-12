"""PyInstaller entry point — dual transport for comfyops-mcp."""
import os
import sys
sys.path.insert(0, "src")

from comfyops_mcp.server import main

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    sys.argv = ["comfyops", "--mode", "http", "--host", host, "--port", str(port)]
main()

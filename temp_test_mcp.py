import sys; sys.path.insert(0, "src")
import os; os.environ["ARXIV_MCP_PORT"] = "10789"; os.environ["ARXIV_MCP_HOST"] = "127.0.0.1"
import uvicorn, asyncio, httpx
from arxiv_mcp.app import build_app
app = build_app()
cfg = uvicorn.Config(app, host="127.0.0.1", port=10789, log_level="warning")
server = uvicorn.Server(cfg)
async def test():
    asyncio.create_task(server.serve())
    await asyncio.sleep(8)
    async with httpx.AsyncClient(base_url="http://127.0.0.1:10789", timeout=10) as cl:
        r = await cl.post("/mcp", json={"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}, headers={"Accept":"application/json, text/event-stream"})
        print("POST /mcp:", r.status_code, r.text[:500])
asyncio.run(test())

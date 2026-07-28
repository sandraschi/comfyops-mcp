import inspect
from fastmcp.server.http import StreamableHTTPASGIApp
print(inspect.getsource(StreamableHTTPASGIApp.__call__))

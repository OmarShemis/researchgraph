import os
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


@asynccontextmanager
async def connect_mcp():
    client = MultiServerMCPClient({
        "local": {"transport": "streamable_http", "url": os.environ["MCP_URL"]},
    })
    async with client.session("local") as session:
        tools = await load_mcp_tools(session)
        yield [tool.model_copy(update={"name": f"mcp_{tool.name}"}) for tool in tools]

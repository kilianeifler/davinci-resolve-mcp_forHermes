"""Read-only probe for Resolve's bundled native MCP server."""

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path("/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolveMCP")


async def main() -> None:
    params = StdioServerParameters(command=str(SERVER), args=[], env={})
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("get_resolve_status", {})
            print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())

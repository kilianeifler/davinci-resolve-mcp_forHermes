"""Live, read-only end-to-end smoke test; requires Resolve to be running."""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "resolve_mcp" / "server.py"


async def main() -> None:
    params = StdioServerParameters(
        command=os.environ["RESOLVE_MCP_PYTHON"],
        args=[str(SERVER)],
        env={
            "RESOLVE_SCRIPT_API": os.environ["RESOLVE_SCRIPT_API"],
            "RESOLVE_SCRIPT_LIB": os.environ["RESOLVE_SCRIPT_LIB"],
            "PYTHONPATH": f"{os.environ['RESOLVE_SCRIPT_API']}/Modules:{ROOT}",
        },
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("resolve_status", {})
            print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())

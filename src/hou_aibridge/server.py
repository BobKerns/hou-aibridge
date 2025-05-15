
from collections.abc import Awaitable
import json
from typing import Any, TypeAlias
import asyncio

from anyio import AsyncFile # type: ignore[import]  # noqa: F401
from aiopath.path import AsyncPath as Path

from mcp.server.fastmcp import FastMCP

'''
A prototype MCP server for the AIBridge project.

This will ultimately communicate with the VSCode extension to provide answers to queries and perform tool actions.

For now, it will just return responses from the responses folder.

It should target Python 3.11+ and use the recommended types such as 'list' and 'dict' instead of 'List' and 'Dict'.
It should use the 'mcp' library rather than reimplementing it on top of FastAPI, specifically the 'mcp.server.fastmcp' module.

'''

RESPONSES_DIR = Path(__file__).parent / "responses"
mcp = FastMCP("hou-aibridge", "0.1.0")


JsonAtomic: TypeAlias = str | int | float | bool | None
JsonArray: TypeAlias = list[JsonAtomic | 'JsonArray' | 'JsonObject']
JsonObject: TypeAlias = dict[str, 'JsonData']
JsonData: TypeAlias = JsonArray | JsonObject | str | int | float | bool | None

RESPONSES: dict[str, Awaitable[JsonData|str]] =  {}

async def load_responses():
    """Load response JSON and Markdown files."""
    async def load_text(f: Path):
        if await f.is_file():
            async with f.open("r", encoding="utf-8") as stream:
                return await stream.read()
    async def load_json(f: Path):
        text = await load_text(f)
        if text:
            return json.loads(text)
    async for f in await RESPONSES_DIR.glob("*.json"):
        if f.suffix == '.json':
            RESPONSES[f.stem] = load_json(f)
        else:
            RESPONSES[f.stem] = load_text(f)


@mcp.tool("query_response")
async def query_response(data: dict[str, Any]) -> dict[str, Any]:
    """Handle a query and return a canned response."""
    query = data.get("query")
    if not query:
        return {"error": "No query provided."}
    return {"response": RESPONSES.get(query, "No response found.")}

@mcp.resource("status://status")
async def status() -> dict[str, Any]:
    """Return server status."""
    return {"status": "ok"}

asyncio.run(load_responses())

def main():

    mcp.run()

if __name__ == "__main__":
    main()

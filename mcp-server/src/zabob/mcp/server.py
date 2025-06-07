# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "aiohttp",
#     "aiopath",
#     "anyio",
#     "click>=8.0.0,<8.2.0",
#     "fastapi",
#     "fastmcp",
#     "httpx",
#     "mcp",
#     "pedantic",
#     "psutil",
#     "semver",
#     "sqlite-vec",
#     "uvicorn",
# ]
# ///

from collections.abc import AsyncGenerator, AsyncIterable, Awaitable
import json
from typing import Any, TypeAlias, TypeVar, cast
import asyncio
import sys

from aiopath.path import AsyncPath as Path
from pathlib import Path as SyncPath

from mcp.server.fastmcp import FastMCP


ROOT = SyncPath(__file__).parent.parent.parent.parent.parent
MCP_VENV = ROOT / 'mcp-server/.venv'
MCP_SRC = ROOT/ 'mcp-server/src'
CORE_SRC = ROOT / 'zabob-modules/src'''
COMMON_SRC = ROOT / 'houdini/zcommon/src'

for p in (MCP_VENV, MCP_SRC, CORE_SRC, COMMON_SRC):
    if not p.exists():
        print(f"Error: {p} does not exist. Please run 'zabob setup' first.", file=sys.stderr)
        sys.exit(1)
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))  # type: ignore[no-redef]

from zabob.core import JsonData

'''
A prototype MCP server for the AIBridge project.

This will ultimately communicate with the VSCode extension to provide answers to queries and perform tool actions.

For now, it will just return responses from the responses folder.

It should target Python 3.11+ and use the recommended types such as 'list' and 'dict' instead of 'List' and 'Dict'.
It should use the 'mcp' library rather than reimplementing it on top of FastAPI, specifically the 'mcp.server.fastmcp' module.

'''

RESPONSES_DIR = Path(__file__).parent / "responses"
PROMPTS_DIR = Path(__file__).parent / "prompts"
INSTRUCTIONS_PATH = SyncPath(__file__).parent / "instructions.md"
with open(INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
    INSTRUCTIONS = f.read()

mcp = FastMCP("zabob", instructions=INSTRUCTIONS)

RESPONSES: dict[str, Awaitable[JsonData|str]] =  {}
PROMPTS: dict[str, Awaitable[JsonData|str]] =  {}



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
    async for f in cast(AsyncIterable[Path], RESPONSES_DIR.glob("*.json")):
        RESPONSES[f.stem] = load_json(f)
    async for f in cast(AsyncIterable[Path], RESPONSES_DIR.glob("*.md")):
        RESPONSES[f.stem] = load_text(f)
    async for f in cast(AsyncIterable[Path], PROMPTS_DIR.glob("*.md")):
        PROMPTS[f.stem] = load_text(f)


T = TypeVar("T")
def awaitable_value(value: T) -> Awaitable[T]:
    async def wrapper() -> AsyncGenerator[T, None]:
        yield  value
    return anext(aiter(wrapper()))

@mcp.tool("query_response")
async def query_response(query: str):
    """Handle a query and return a canned response."""
    return {"response": f'{RESPONSES_DIR}.json'}
    if not query:
        return {"error": "No query provided."}
    return {"response": await RESPONSES.get(query, awaitable_value("No response found."))}

@mcp.resource("status://status")
async def status() -> dict[str, Any]:
    """Return server status."""
    return {"status": "ok"}

@mcp.resource('sop://info')
def sop_info():
    """Return SOP info."""
    return {
        "name": "SOP",
        "version": "1.0.0",
        "description": "Standard Operating Procedure for AIBridge.",
        "author": "AIBridge Team"
    }

@mcp.prompt("prompt://prompt")
async def prompt(prompt: str, data: dict[str, Any]) -> dict[str, Any]:
    """Handle a prompt and return a canned response."""
    if not prompt:
        return {"error": "No prompt provided."}
    return {"response": await PROMPTS.get(prompt, awaitable_value("No response found."))}

asyncio.run(load_responses())

def main():

    mcp.run()

if __name__ == "__main__":
    main()

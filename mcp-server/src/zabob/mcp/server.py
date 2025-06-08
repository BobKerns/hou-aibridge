#!/usr/bin/env uv run --script
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
'''
A prototype MCP server for the AIBridge project.

This will ultimately communicate with the VSCode extension to provide answers to queries and perform tool actions.

For now, it will just return responses from the responses folder.

It should target Python 3.11+ and use the recommended types such as 'list' and 'dict' instead of 'List' and 'Dict'.
It should use the 'mcp' library rather than reimplementing it on top of FastAPI, specifically the 'mcp.server.fastmcp' module.

'''

from collections.abc import AsyncGenerator, AsyncIterable, Awaitable
import json
from typing import Any, TypeVar, cast, TypedDict
import asyncio
import sys
import click
import httpx
import logging

from aiopath.path import AsyncPath as Path
from pathlib import Path as SyncPath

from mcp.server.fastmcp import FastMCP


ROOT = SyncPath(__file__).parent.parent.parent.parent.parent
MCP_SRC = ROOT/ 'mcp-server/src'
CORE_SRC = ROOT / 'zabob-modules/src'
COMMON_SRC = ROOT / 'houdini/zcommon/src'

# Check for source directories (but not .venv in Docker)
for p in (MCP_SRC, CORE_SRC, COMMON_SRC):
    if not p.exists():
        print(f"Error: {p} does not exist. Please run 'zabob setup' first.", file=sys.stderr)
        sys.exit(1)
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))  # type: ignore[no-redef]

from zabob.core import JsonData
from zabob.mcp.database import HoudiniDatabase

# TypedDict definitions for better type safety
class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str

class WebSearchResponse(TypedDict):
    query: str
    results: list[SearchResult]
    error: str | None

class NodeTypeInfo(TypedDict):
    name: str
    category: str
    description: str
    inputs: str
    outputs: int
    is_generator: bool

class EnhancedNodeTypeInfo(NodeTypeInfo):
    documentation_search: list[SearchResult]
    official_docs: dict[str, Any] | None

class FunctionInfo(TypedDict):
    name: str
    module: str
    datatype: str
    docstring: str

class EnhancedFunctionInfo(FunctionInfo):
    example_search: list[SearchResult]
    hom_docs: dict[str, Any] | None



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

# Initialize database connection
db = HoudiniDatabase()

# Web search integration helpers
async def vscode_websearchforcopilot_webSearch(query: str, num_results: int = 5) -> dict[str, Any]:
    """Perform web search using DuckDuckGo instant answer API."""
    try:
        # Use DuckDuckGo's instant answer API (no API key required)
        async with httpx.AsyncClient() as client:
            # DuckDuckGo instant answer API
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }

            response = await client.get(
                "https://api.duckduckgo.com/",
                params=params,
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                # Extract abstract/definition if available
                if data.get("Abstract"):
                    results.append({
                        "title": data.get("AbstractText", query),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", "")[:300]
                    })

                # Extract related topics
                for topic in data.get("RelatedTopics", [])[:num_results-len(results)]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", "")[:200]
                        })

                # If no results, create a basic search result
                if not results:
                    results.append({
                        "title": f"Search results for '{query}'",
                        "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                        "snippet": f"No direct results found. Try searching on DuckDuckGo for more information about '{query}'."
                    })

                return {
                    "query": query,
                    "results": results[:num_results],
                    "error": None
                }
            else:
                logging.warning(f"DuckDuckGo API returned status {response.status_code}")
                return {
                    "query": query,
                    "results": [{
                        "title": f"Search for '{query}'",
                        "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                        "snippet": "Search results available on DuckDuckGo"
                    }],
                    "error": None
                }

    except Exception as e:
        logging.error(f"Web search failed: {e}")
        return {
            "query": query,
            "results": [{
                "title": f"Search for '{query}'",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "snippet": "Search functionality temporarily unavailable"
            }],
            "error": str(e)
        }

async def fetch_webpage(urls: list[str], query: str) -> str:
    """Fetch content from web pages."""
    try:
        async with httpx.AsyncClient() as client:
            for url in urls:
                try:
                    response = await client.get(url, timeout=10.0)
                    if response.status_code == 200:
                        # Simple text extraction (in practice, you'd want better HTML parsing)
                        content = response.text
                        # Return first 1000 characters as preview
                        return content[:1000] if len(content) > 1000 else content
                except Exception as e:
                    logging.warning(f"Failed to fetch {url}: {e}")
                    continue
        return "No content could be fetched from provided URLs"
    except Exception as e:
        logging.error(f"Webpage fetch failed: {e}")
        return f"Fetch error: {str(e)}"

@mcp.tool("get_functions_returning_nodes")
async def get_functions_returning_nodes():
    """Find functions that return Houdini node objects."""
    try:
        with db:
            functions = db.get_functions_returning_nodes()
            return {
                "functions": [
                    {
                        "name": f.name,
                        "module": f.module,
                        "datatype": f.datatype,
                        "docstring": f.docstring[:200] + "..." if f.docstring and len(f.docstring) > 200 else f.docstring
                    }
                    for f in functions
                ],
                "count": len(functions)
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("search_functions")
async def search_functions(keyword: str, limit: int = 20):
    """Search for functions by keyword in name or docstring."""
    if not keyword:
        return {"error": "No keyword provided."}

    try:
        with db:
            functions = db.search_functions_by_keyword(keyword, limit)
            return {
                "keyword": keyword,
                "functions": [
                    {
                        "name": f.name,
                        "module": f.module,
                        "datatype": f.datatype,
                        "docstring": f.docstring[:200] + "..." if f.docstring and len(f.docstring) > 200 else f.docstring
                    }
                    for f in functions
                ],
                "count": len(functions)
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("get_primitive_functions")
async def get_primitive_functions():
    """Find functions related to primitive operations (selection, manipulation, etc.)."""
    try:
        with db:
            functions = db.get_primitive_related_functions()
            return {
                "functions": [
                    {
                        "name": f.name,
                        "module": f.module,
                        "datatype": f.datatype,
                        "docstring": f.docstring[:200] + "..." if f.docstring and len(f.docstring) > 200 else f.docstring
                    }
                    for f in functions
                ],
                "count": len(functions)
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("get_modules_summary")
async def get_modules_summary():
    """Get a summary of all Houdini modules with function counts."""
    try:
        with db:
            modules = db.get_modules_summary()
            return {
                "modules": [
                    {
                        "name": m.name,
                        "status": m.status,
                        "function_count": m.function_count,
                        "file": m.file
                    }
                    for m in modules[:50]  # Limit to first 50 for readability
                ],
                "total_count": len(modules)
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("search_node_types")
async def search_node_types(keyword: str, limit: int = 20):
    """Search for node types by keyword in name or description."""
    if not keyword:
        return {"error": "No keyword provided."}

    try:
        with db:
            node_types = db.search_node_types(keyword, limit)
            return {
                "keyword": keyword,
                "node_types": [
                    {
                        "name": nt.name,
                        "category": nt.category,
                        "description": nt.description,
                        "inputs": f"{nt.min_inputs}-{nt.max_inputs}",
                        "outputs": nt.max_outputs,
                        "is_generator": nt.is_generator
                    }
                    for nt in node_types
                ],
                "count": len(node_types)
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("enhanced_search_node_types")
async def enhanced_search_node_types(keyword: str, include_docs: bool = True, limit: int = 5):
    """Search node types with optional live documentation integration."""
    try:
        with db:
            # Get static database results
            node_types = db.search_node_types(keyword, limit)

            basic_results = []
            for nt in node_types:
                basic_results.append({
                    "name": nt.name,
                    "category": nt.category,
                    "description": nt.description,
                    "inputs": f"{nt.min_inputs}-{nt.max_inputs}",
                    "outputs": nt.max_outputs,
                    "is_generator": nt.is_generator
                })

            result = {
                "keyword": keyword,
                "node_types": basic_results,
                "count": len(node_types)
            }

            if include_docs and node_types:
                # Enhance top 3 results with live documentation
                enhanced_nodes = []

                for node in node_types[:3]:
                    enhanced_node: dict[str, Any] = {
                        "name": node.name,
                        "category": node.category,
                        "description": node.description,
                        "inputs": f"{node.min_inputs}-{node.max_inputs}",
                        "outputs": node.max_outputs,
                        "is_generator": node.is_generator
                    }

                    # Use web search to find documentation
                    search_query = f"Houdini {node.name} {node.category} node documentation examples"
                    search_results = await vscode_websearchforcopilot_webSearch(search_query)
                    enhanced_node["documentation_search"] = search_results.get("results", [])[:3]

                    # Try to fetch SideFX official documentation
                    if node.category.lower() in ['sop', 'top', 'object', 'dop']:
                        doc_url = f"https://www.sidefx.com/docs/houdini/nodes/{node.category.lower()}/{node.name}.html"
                        try:
                            doc_content = await fetch_webpage([doc_url], f"{node.name} node documentation")
                            official_docs: dict[str, Any] = {
                                "url": doc_url,
                                "content_preview": doc_content[:400] + "..." if len(doc_content) > 400 else doc_content
                            }
                            enhanced_node["official_docs"] = official_docs
                        except:
                            failed_docs: dict[str, Any] = {"url": doc_url, "status": "fetch_failed"}
                            enhanced_node["official_docs"] = failed_docs

                    enhanced_nodes.append(enhanced_node)

                result["enhanced_results"] = enhanced_nodes
                result["enhancement_note"] = "Top results enhanced with live documentation"

            return result

    except Exception as e:
        return {"error": f"Enhanced search failed: {str(e)}"}

@mcp.tool("enhanced_search_functions")
async def enhanced_search_functions(keyword: str, include_examples: bool = True, limit: int = 5):
    """Search functions with optional code examples and documentation."""
    try:
        with db:
            # Get static database results
            functions = db.search_functions_by_keyword(keyword, limit)

            basic_results = []
            for f in functions:
                basic_results.append({
                    "name": f.name,
                    "module": f.module,
                    "datatype": f.datatype,
                    "docstring": f.docstring[:200] + "..." if f.docstring and len(f.docstring) > 200 else f.docstring
                })

            result = {
                "keyword": keyword,
                "functions": basic_results,
                "count": len(functions)
            }

            if include_examples and functions:
                # Enhance top 3 functions with examples
                enhanced_functions = []

                for func in functions[:3]:
                    enhanced_func: dict[str, Any] = {
                        "name": func.name,
                        "module": func.module,
                        "datatype": func.datatype,
                        "docstring": func.docstring[:200] + "..." if func.docstring and len(func.docstring) > 200 else func.docstring
                    }

                    # Search for code examples and tutorials
                    example_query = f"Houdini Python {func.name} code examples tutorial"
                    search_results = await vscode_websearchforcopilot_webSearch(example_query)
                    enhanced_func["example_search"] = search_results.get("results", [])[:3]

                    # Try to fetch official HOM documentation
                    if func.module == "hou":
                        # Build HOM documentation URL
                        doc_url = f"https://www.sidefx.com/docs/houdini/hom/hou/{func.name}.html"
                        try:
                            doc_content = await fetch_webpage([doc_url], f"{func.name} function documentation")
                            hom_docs: dict[str, Any] = {
                                "url": doc_url,
                                "content_preview": doc_content[:400] + "..." if len(doc_content) > 400 else doc_content
                            }
                            enhanced_func["hom_docs"] = hom_docs
                        except:
                            failed_hom_docs: dict[str, Any] = {"url": doc_url, "status": "fetch_failed"}
                            enhanced_func["hom_docs"] = failed_hom_docs

                    enhanced_functions.append(enhanced_func)

                result["enhanced_results"] = enhanced_functions
                result["enhancement_note"] = "Top results enhanced with code examples and documentation"

            return result

    except Exception as e:
        return {"error": f"Enhanced function search failed: {str(e)}"}

@mcp.tool("web_search_houdini")
async def web_search_houdini(query: str, num_results: int = 5):
    """Perform a web search specifically for Houdini-related content."""
    if not query:
        return {"error": "No query provided."}

    try:
        # Enhance query with Houdini context
        enhanced_query = f"Houdini 3D software {query}"
        search_results = await vscode_websearchforcopilot_webSearch(enhanced_query, num_results)

        return {
            "original_query": query,
            "enhanced_query": enhanced_query,
            "results": search_results.get("results", []),
            "count": len(search_results.get("results", []))
        }
    except Exception as e:
        return {"error": f"Web search failed: {str(e)}"}

@mcp.tool("fetch_houdini_docs")
async def fetch_houdini_docs(doc_type: str, node_name: str = "", function_name: str = ""):
    """Fetch official Houdini documentation for nodes or functions."""
    if not doc_type:
        return {"error": "No documentation type provided (node, function, or tutorial)."}

    try:
        urls = []

        if doc_type == "node" and node_name:
            # Try common node categories
            for category in ['sop', 'top', 'object', 'dop', 'chop', 'cop2']:
                urls.append(f"https://www.sidefx.com/docs/houdini/nodes/{category}/{node_name}.html")

        elif doc_type == "function" and function_name:
            urls.append(f"https://www.sidefx.com/docs/houdini/hom/hou/{function_name}.html")

        elif doc_type == "tutorial":
            # Search for tutorials
            tutorial_query = f"Houdini tutorial {node_name or function_name}"
            search_results = await vscode_websearchforcopilot_webSearch(tutorial_query)
            return {
                "doc_type": doc_type,
                "search_query": tutorial_query,
                "tutorial_results": search_results.get("results", [])[:5]
            }

        if urls:
            content = await fetch_webpage(urls, f"{doc_type} documentation")
            return {
                "doc_type": doc_type,
                "target": node_name or function_name,
                "urls_tried": urls,
                "content": content
            }
        else:
            return {"error": "Invalid parameters for documentation fetch."}

    except Exception as e:
        return {"error": f"Documentation fetch failed: {str(e)}"}

@mcp.tool("pdg_workflow_assistant")
async def pdg_workflow_assistant(workflow_description: str):
    """Get PDG components and workflow guidance for a specific task."""
    try:
        with db:
            # Extract keywords and search PDG registry
            keywords = workflow_description.lower().split()
            relevant_entries = []

            for keyword in keywords[:3]:  # Limit to avoid too many queries
                entries = db.search_pdg_registry(keyword, limit=5)
                relevant_entries.extend(entries)

            # Remove duplicates while preserving order
            seen = set()
            unique_entries = []
            for entry in relevant_entries:
                if entry.name not in seen:
                    seen.add(entry.name)
                    unique_entries.append(entry)

            result = {
                "workflow_description": workflow_description,
                "pdg_components": [
                    {
                        "name": entry.name,
                        "registry": entry.registry
                    }
                    for entry in unique_entries[:10]
                ],
                "count": len(unique_entries)
            }

            # Enhance with web search for workflow guidance
            workflow_query = f"Houdini PDG workflow {workflow_description} tutorial"
            search_results = await vscode_websearchforcopilot_webSearch(workflow_query)
            result["workflow_guidance"] = search_results.get("results", [])[:3]

            return result

    except Exception as e:
        return {"error": f"PDG workflow assistance failed: {str(e)}"}

@mcp.tool("get_node_types_by_category")
async def get_node_types_by_category(category: str = ""):
    """Get node types, optionally filtered by category (e.g., 'Sop', 'Object', 'Dop')."""
    try:
        with db:
            if category:
                node_types = db.get_node_types_by_category(category)
            else:
                node_types = db.get_node_types_by_category()[:50]  # Limit if no category

            return {
                "category": category or "all",
                "node_types": [
                    {
                        "name": nt.name,
                        "category": nt.category,
                        "description": nt.description,
                        "inputs": f"{nt.min_inputs}-{nt.max_inputs}",
                        "outputs": nt.max_outputs,
                        "is_generator": nt.is_generator
                    }
                    for nt in node_types
                ],
                "count": len(node_types)
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("get_database_stats")
async def get_database_stats():
    """Get statistics about the Houdini database contents."""
    try:
        with db:
            stats = db.get_database_stats()
            return {
                "database_path": str(db.db_path),
                "statistics": stats
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("get_pdg_registry")
async def get_pdg_registry(registry_type: str | None = None):
    """Get PDG (TOPs) registry entries, optionally filtered by registry type (Node, Scheduler, Service, etc.)."""
    try:
        with db:
            entries = db.get_pdg_registry(registry_type)
            return {
                "entries": [
                    {
                        "name": entry.name,
                        "registry": entry.registry
                    }
                    for entry in entries
                ],
                "count": len(entries),
                "registry_type": registry_type or "all"
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("search_pdg_registry")
async def search_pdg_registry(keyword: str, limit: int = 50):
    """Search PDG registry entries by keyword in name."""
    try:
        with db:
            entries = db.search_pdg_registry(keyword, limit)
            return {
                "entries": [
                    {
                        "name": entry.name,
                        "registry": entry.registry
                    }
                    for entry in entries
                ],
                "count": len(entries),
                "keyword": keyword
            }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}

@mcp.tool("query_response")
async def query_response(query: str):
    """Handle a general query and return a canned response (legacy tool)."""
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

@click.command()
@click.option('--help-tools', is_flag=True, help='Show detailed information about available MCP tools and exit')
def main(help_tools: bool = False):
    """
    Available MCP Tools:
    • get_functions_returning_nodes    - Find functions that return Houdini node objects
    • search_functions                 - Search functions by keyword in name or docstring
    • enhanced_search_functions        - Search functions with optional code examples and documentation
    • get_primitive_functions          - Find functions related to primitive operations
    • get_modules_summary              - Get summary of all Houdini modules with function counts
    • search_node_types               - Search node types by keyword
    • enhanced_search_node_types      - Search node types with optional live documentation integration
    • get_node_types_by_category      - Get node types filtered by category (Sop, Object, Dop, etc.)
    • get_database_stats              - Get statistics about the Houdini database contents
    • get_pdg_registry                - Get PDG registry entries
    • search_pdg_registry             - Search PDG registry entries by keyword
    • pdg_workflow_assistant          - Get PDG components and workflow guidance for tasks
    • web_search_houdini              - Perform web search specifically for Houdini-related content
    • fetch_houdini_docs              - Fetch official Houdini documentation for nodes or functions
    • query_response                  - Handle general queries (legacy tool)

    Database: {db.db_path if hasattr(db, 'db_path') else 'Not initialized'}

    Usage:
    This server starts an MCP (Model Context Protocol) server that provides
    AI agents with access to comprehensive Houdini Python API information.

    The server waits for MCP client connections and responds to tool requests
    with data from the Houdini modules database, enhanced with live web search
    and documentation fetching capabilities.
    """

    def echo(*args, err: bool=True, **kwargs):
        """
        click.echo, but to stderr by default.
        """
        click.echo(*args, **kwargs, err=err)
    if help_tools:
        echo("🔧 Zabob MCP Server - Available Tools:\n")
        tools = [
            ("get_functions_returning_nodes", "Find functions that return Houdini node objects"),
            ("search_functions", "Search functions by keyword (requires: keyword, optional: limit)"),
            ("enhanced_search_functions", "Search functions with code examples and docs (requires: keyword, optional: include_examples, limit)"),
            ("get_primitive_functions", "Find functions related to primitive operations"),
            ("get_modules_summary", "Get summary of all Houdini modules with function counts"),
            ("search_node_types", "Search node types by keyword (requires: keyword, optional: limit)"),
            ("enhanced_search_node_types", "Search node types with live documentation (requires: keyword, optional: include_docs, limit)"),
            ("get_node_types_by_category", "Get node types by category (optional: category)"),
            ("get_database_stats", "Get statistics about the Houdini database contents"),
            ("get_pdg_registry", "Get PDG registry entries (optional: registry_type)"),
            ("search_pdg_registry", "Search PDG registry entries by keyword (requires: keyword, optional: limit)"),
            ("pdg_workflow_assistant", "Get PDG components and workflow guidance (requires: workflow_description)"),
            ("web_search_houdini", "Perform web search for Houdini content (requires: query, optional: num_results)"),
            ("fetch_houdini_docs", "Fetch official Houdini documentation (requires: doc_type, optional: node_name, function_name)"),
            ("query_response", "Handle general queries (requires: query)")
        ]

        for tool_name, description in tools:
            echo(f"  {tool_name:30} - {description}")

        echo(f"\n📊 Database: {db.db_path if hasattr(db, 'db_path') else 'Not initialized'}")
        echo("\n🚀 To start the MCP server, run without arguments.")
        return

    echo("🚀 Starting Zabob MCP Server...")
    echo(f"📊 Database: {db.db_path if hasattr(db, 'db_path') else 'Not initialized'}")
    echo("🔗 Waiting for MCP client connections...")
    mcp.run()

if __name__ == "__main__":
    main()

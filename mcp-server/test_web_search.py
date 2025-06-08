#!/usr/bin/env python3
"""
Quick test script for the web search functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add the source directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from zabob.mcp.server import vscode_websearchforcopilot_webSearch

async def test_search():
    """Test the web search functionality."""
    print("🔍 Testing web search functionality...")

    # Test search for Houdini-related content
    query = "Houdini VEX"
    results = await vscode_websearchforcopilot_webSearch(query, num_results=3)

    print(f"\n📝 Query: {query}")
    print(f"📊 Results found: {len(results.get('results', []))}")

    for i, result in enumerate(results.get('results', [])[:3], 1):
        print(f"\n{i}. {result.get('title', 'No title')}")
        print(f"   🔗 {result.get('url', 'No URL')}")
        print(f"   📄 {result.get('snippet', 'No snippet')[:100]}...")

    if results.get('error'):
        print(f"\n⚠️  Error: {results['error']}")
    else:
        print("\n✅ Web search test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_search())

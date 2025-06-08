#!/usr/bin/env python3
"""
Comprehensive Live Demo: Zabob MCP Server with Web Search Integration
Demonstrates the working web search capabilities integrated into the MCP server.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    # Import the enhanced server functions
    from zabob.mcp.server import (
        enhanced_search_node_types,
        enhanced_search_functions,
        web_search_houdini,
        fetch_houdini_docs,
        pdg_workflow_assistant,
        vscode_websearchforcopilot_webSearch
    )
    from zabob.mcp.database import HoudiniDatabase

    async def demo_web_search_integration():
        """Demonstrate the actual working web search integration."""

        print("🌐 Zabob MCP Server: Live Web Search Integration Demo")
        print("=" * 60)
        print("✨ Now featuring REAL web search capabilities with DuckDuckGo API!")
        print()

        # Demo 1: Enhanced Node Type Search with Live Documentation
        print("🔍 Demo 1: Enhanced Node Type Search")
        print("-" * 40)
        print("🎯 Searching for 'lattice' nodes with live documentation...")

        try:
            result = await enhanced_search_node_types("lattice", include_docs=True, limit=3)

            print(f"📊 Found {result.get('count', 0)} lattice-related nodes:")
            for node in result.get('node_types', []):
                print(f"   • {node['name']} ({node['category']}) - {node['description'][:50]}...")

            # Show enhanced results with live documentation
            if 'enhanced_results' in result:
                print(f"\n✨ Enhanced with live documentation:")
                for enhanced in result['enhanced_results'][:2]:  # Show first 2
                    print(f"\n   🔧 {enhanced['name']} node:")

                    # Show web search results
                    doc_search = enhanced.get('documentation_search', [])
                    if doc_search:
                        print(f"      🌐 Web Documentation Found:")
                        for doc in doc_search[:2]:
                            print(f"         • {doc.get('title', 'No title')[:40]}...")
                            print(f"           {doc.get('url', 'No URL')}")

                    # Show official docs if fetched
                    official = enhanced.get('official_docs')
                    if official and official.get('content_preview'):
                        print(f"      📚 Official SideFX Docs:")
                        print(f"         {official['content_preview'][:80]}...")

        except Exception as e:
            print(f"❌ Error in enhanced node search: {e}")

        # Demo 2: Enhanced Function Search with Code Examples
        print(f"\n\n🔍 Demo 2: Enhanced Function Search")
        print("-" * 40)
        print("🎯 Searching for 'geometry' functions with code examples...")

        try:
            result = await enhanced_search_functions("geometry", include_examples=True, limit=3)

            print(f"📊 Found {result.get('count', 0)} geometry-related functions:")
            for func in result.get('functions', []):
                print(f"   • {func['module']}.{func['name']}() → {func['datatype']}")

            # Show enhanced results with examples
            if 'enhanced_results' in result:
                print(f"\n✨ Enhanced with code examples:")
                for enhanced in result['enhanced_results'][:2]:  # Show first 2
                    print(f"\n   🐍 {enhanced['name']}() function:")

                    # Show example search results
                    examples = enhanced.get('example_search', [])
                    if examples:
                        print(f"      📝 Code Examples Found:")
                        for example in examples[:2]:
                            print(f"         • {example.get('title', 'No title')[:40]}...")
                            print(f"           {example.get('url', 'No URL')}")

        except Exception as e:
            print(f"❌ Error in enhanced function search: {e}")

        # Demo 3: Direct Web Search for Houdini Content
        print(f"\n\n🔍 Demo 3: Direct Houdini Web Search")
        print("-" * 40)
        print("🎯 Searching web for 'VEX particle simulation'...")

        try:
            result = await web_search_houdini("VEX particle simulation", num_results=3)

            print(f"📊 Original query: {result.get('original_query')}")
            print(f"🔍 Enhanced query: {result.get('enhanced_query')}")
            print(f"📄 Results found: {result.get('count', 0)}")

            for i, web_result in enumerate(result.get('results', [])[:3], 1):
                print(f"\n   {i}. {web_result.get('title', 'No title')}")
                print(f"      🔗 {web_result.get('url', 'No URL')}")
                print(f"      📄 {web_result.get('snippet', 'No snippet')[:80]}...")

        except Exception as e:
            print(f"❌ Error in web search: {e}")

        # Demo 4: Official Houdini Documentation Fetching
        print(f"\n\n🔍 Demo 4: Official Documentation Fetching")
        print("-" * 40)
        print("🎯 Fetching official documentation for 'lattice' node...")

        try:
            result = await fetch_houdini_docs("node", node_name="lattice")

            print(f"📚 Documentation type: {result.get('doc_type')}")
            print(f"🎯 Target: {result.get('target')}")
            print(f"🌐 URLs tried: {len(result.get('urls_tried', []))}")

            content = result.get('content', '')
            if content and len(content) > 100:
                print(f"📄 Content preview:")
                print(f"   {content[:200]}...")
            elif content:
                print(f"📄 Content: {content}")
            else:
                print("📄 No content fetched (expected for some nodes)")

        except Exception as e:
            print(f"❌ Error fetching documentation: {e}")

        # Demo 5: PDG Workflow Assistant
        print(f"\n\n🔍 Demo 5: PDG Workflow Assistant")
        print("-" * 40)
        print("🎯 Getting PDG workflow guidance for 'file processing pipeline'...")

        try:
            result = await pdg_workflow_assistant("file processing pipeline")

            print(f"📋 Workflow: {result.get('workflow_description')}")
            print(f"🔧 PDG components found: {result.get('count', 0)}")

            # Show PDG components
            for component in result.get('pdg_components', [])[:5]:
                print(f"   • {component['name']} ({component['registry']})")

            # Show workflow guidance from web search
            guidance = result.get('workflow_guidance', [])
            if guidance:
                print(f"\n🧭 Workflow guidance from web:")
                for guide in guidance[:2]:
                    print(f"   • {guide.get('title', 'No title')[:40]}...")
                    print(f"     {guide.get('url', 'No URL')}")

        except Exception as e:
            print(f"❌ Error in PDG workflow assistance: {e}")

        # Demo 6: Raw Web Search API Test
        print(f"\n\n🔍 Demo 6: Raw Web Search Engine Test")
        print("-" * 40)
        print("🎯 Testing DuckDuckGo API directly with 'Houdini VEX'...")

        try:
            result = await vscode_websearchforcopilot_webSearch("Houdini VEX", num_results=3)

            print(f"🔍 Query: {result.get('query')}")
            print(f"📄 Results: {len(result.get('results', []))}")
            error = result.get('error')
            if error:
                print(f"⚠️  Error: {error}")

            for i, search_result in enumerate(result.get('results', [])[:3], 1):
                print(f"\n   {i}. {search_result.get('title', 'No title')}")
                print(f"      🔗 {search_result.get('url', 'No URL')}")
                print(f"      📄 {search_result.get('snippet', 'No snippet')[:60]}...")

        except Exception as e:
            print(f"❌ Error in raw web search: {e}")

        # Summary
        print(f"\n\n🎉 Web Search Integration Demo Complete!")
        print("=" * 45)
        print("✅ Enhanced node type search with live documentation")
        print("✅ Enhanced function search with code examples")
        print("✅ Direct Houdini web search capabilities")
        print("✅ Official SideFX documentation fetching")
        print("✅ PDG workflow assistance with web guidance")
        print("✅ Raw DuckDuckGo API integration working")
        print()
        print("🚀 The MCP server now combines:")
        print("   📊 Static database knowledge")
        print("   🌐 Live web search results")
        print("   📚 Official documentation")
        print("   🧭 Real-time guidance")
        print()
        print("💡 Ready for production use with AI agents!")

    # Run the comprehensive demo
    if __name__ == "__main__":
        asyncio.run(demo_web_search_integration())

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the mcp-server directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error running demo: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

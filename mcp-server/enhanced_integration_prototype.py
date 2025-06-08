#!/usr/bin/env python3
"""
Prototype: Enhanced MCP Tools with Live Documentation Integration
Shows how to extend current tools with web search and fetch capabilities
"""

import sys
import asyncio
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Simulated enhanced tools (would integrate with actual MCP server)
class EnhancedMCPTools:
    """Prototype showing enhanced MCP tools with documentation integration."""

    def __init__(self):
        # These would be real MCP tools in actual implementation
        self.web_search = self._mock_web_search
        self.fetch_webpage = self._mock_fetch_webpage

    def _mock_web_search(self, query):
        """Mock web search - would use real vscode-websearchforcopilot_webSearch tool."""
        return {
            "results": [
                f"SideFX Documentation: {query}",
                f"Houdini Community Tutorial: {query}",
                f"CGWiki Examples: {query}"
            ]
        }

    def _mock_fetch_webpage(self, url):
        """Mock webpage fetch - would use real fetch_webpage tool."""
        return f"Documentation content for {url} with examples and parameters..."

    async def enhanced_search_node_types(self, keyword, include_docs=True):
        """Enhanced node search with live documentation."""
        # Step 1: Get static database results (existing functionality)
        from zabob.mcp.database import HoudiniDatabase

        with HoudiniDatabase() as db:
            static_nodes = db.search_node_types(keyword, limit=5)

        result = {
            "keyword": keyword,
            "static_results": [
                {
                    "name": nt.name,
                    "category": nt.category,
                    "description": nt.description
                }
                for nt in static_nodes
            ],
            "count": len(static_nodes)
        }

        if include_docs and static_nodes:
            # Step 2: Enhance with live documentation
            enhanced_results = []

            for node in static_nodes[:3]:  # Enhance top 3 results
                enhanced_node = {
                    "name": node.name,
                    "category": node.category,
                    "description": node.description
                }

                # Fetch live documentation
                doc_query = f"Houdini {node.name} node documentation examples"
                search_results = self.web_search(doc_query)
                enhanced_node["documentation_links"] = search_results["results"]

                # Try to fetch specific SideFX documentation
                sidefx_url = f"https://www.sidefx.com/docs/houdini/nodes/sop/{node.name}.html"
                doc_content = self.fetch_webpage(sidefx_url)
                enhanced_node["live_documentation"] = doc_content[:200] + "..."

                enhanced_results.append(enhanced_node)

            result["enhanced_results"] = enhanced_results

        return result

    async def enhanced_search_functions(self, keyword, include_examples=True):
        """Enhanced function search with code examples."""
        # Step 1: Static database query
        from zabob.mcp.database import HoudiniDatabase

        with HoudiniDatabase() as db:
            static_functions = db.search_functions_by_keyword(keyword, limit=5)

        result = {
            "keyword": keyword,
            "static_results": [
                {
                    "name": f.name,
                    "module": f.module,
                    "docstring": f.docstring
                }
                for f in static_functions
            ],
            "count": len(static_functions)
        }

        if include_examples and static_functions:
            # Step 2: Get live examples and tutorials
            enhanced_results = []

            for func in static_functions[:3]:
                enhanced_func = {
                    "name": func.name,
                    "module": func.module,
                    "docstring": func.docstring
                }

                # Search for code examples
                example_query = f"Houdini Python {func.name} code examples tutorial"
                search_results = self.web_search(example_query)
                enhanced_func["tutorial_links"] = search_results["results"]

                # Try to fetch official documentation
                if func.module == "hou":
                    doc_url = f"https://www.sidefx.com/docs/houdini/hom/hou/{func.name}.html"
                    doc_content = self.fetch_webpage(doc_url)
                    enhanced_func["official_documentation"] = doc_content[:300] + "..."

                enhanced_results.append(enhanced_func)

            result["enhanced_results"] = enhanced_results

        return result

    async def enhanced_pdg_guidance(self, workflow_query):
        """Enhanced PDG assistance with workflow guidance."""
        # Step 1: Check PDG registry
        from zabob.mcp.database import HoudiniDatabase

        with HoudiniDatabase() as db:
            # Extract keywords from query
            keywords = workflow_query.lower().split()
            relevant_entries = []

            for keyword in keywords:
                entries = db.search_pdg_registry(keyword, limit=3)
                relevant_entries.extend(entries)

        result = {
            "query": workflow_query,
            "relevant_pdg_components": [
                {"name": e.name, "registry": e.registry}
                for e in relevant_entries[:5]
            ]
        }

        # Step 2: Get workflow tutorials and examples
        tutorial_query = f"Houdini PDG {workflow_query} tutorial workflow"
        search_results = self.web_search(tutorial_query)
        result["workflow_tutorials"] = search_results["results"]

        # Step 3: Fetch specific PDG documentation
        pdg_doc_url = "https://www.sidefx.com/docs/houdini/tops/index.html"
        pdg_content = self.fetch_webpage(pdg_doc_url)
        result["pdg_documentation_context"] = pdg_content[:400] + "..."

        return result

async def demo_enhanced_capabilities():
    """Demonstrate the enhanced capabilities."""
    print("🚀 Enhanced MCP Tools Demo with Live Documentation")
    print("=" * 55)

    tools = EnhancedMCPTools()

    # Demo 1: Enhanced node search
    print("\n📋 Demo 1: Enhanced Node Search")
    print("-" * 35)
    result1 = await tools.enhanced_search_node_types("deform")

    print(f"Query: 'deform' nodes")
    print(f"Static results: {result1['count']} nodes found")
    for node in result1['static_results'][:2]:
        print(f"  • {node['name']} ({node['category']})")

    if 'enhanced_results' in result1:
        print(f"\n✨ Enhanced with documentation:")
        for node in result1['enhanced_results'][:1]:
            print(f"  📚 {node['name']} documentation:")
            for link in node['documentation_links'][:2]:
                print(f"    • {link}")
            print(f"    📖 Live content preview: {node['live_documentation']}")

    # Demo 2: Enhanced function search
    print("\n\n📋 Demo 2: Enhanced Function Search")
    print("-" * 37)
    result2 = await tools.enhanced_search_functions("geometry")

    print(f"Query: 'geometry' functions")
    print(f"Static results: {result2['count']} functions found")
    for func in result2['static_results'][:2]:
        print(f"  • {func['name']} ({func['module']})")

    if 'enhanced_results' in result2:
        print(f"\n✨ Enhanced with examples:")
        for func in result2['enhanced_results'][:1]:
            print(f"  🔧 {func['name']} examples:")
            for link in func['tutorial_links'][:2]:
                print(f"    • {link}")
            if 'official_documentation' in func:
                print(f"    📖 Official docs: {func['official_documentation']}")

    # Demo 3: PDG workflow guidance
    print("\n\n📋 Demo 3: PDG Workflow Guidance")
    print("-" * 34)
    result3 = await tools.enhanced_pdg_guidance("file processing batch render")

    print(f"Query: '{result3['query']}'")
    print(f"Relevant PDG components:")
    for comp in result3['relevant_pdg_components'][:3]:
        print(f"  • {comp['name']} ({comp['registry']})")

    print(f"\n✨ Workflow tutorials:")
    for tutorial in result3['workflow_tutorials'][:2]:
        print(f"  • {tutorial}")

    print(f"\n📖 PDG context: {result3['pdg_documentation_context']}")

def show_implementation_plan():
    """Show how to implement this in the actual MCP server."""
    print(f"\n\n🛠️  Implementation Plan for Actual MCP Server")
    print("=" * 50)

    print("""
    1. Enhance existing MCP tools in server.py:

    @mcp.tool("enhanced_search_node_types")
    async def enhanced_search_node_types(keyword: str, include_docs: bool = True):
        # Get static results from database
        static_results = db.search_node_types(keyword)

        if include_docs:
            # Use web search tool
            search_results = await vscode_websearchforcopilot_webSearch(
                f"Houdini {keyword} node documentation"
            )

            # Use fetch tool for specific documentation
            for node in static_results[:3]:
                doc_url = f"https://www.sidefx.com/docs/houdini/nodes/sop/{node.name}.html"
                doc_content = await fetch_webpage([doc_url], "node documentation")
                # Combine static + live data

        return enhanced_response

    2. Add new documentation-focused tools:
       • get_node_documentation(node_name)
       • get_function_examples(function_name)
       • get_pdg_workflow_guide(workflow_type)

    3. Update demo scripts to showcase live integration
    """)

async def main():
    """Run the enhanced demo."""
    await demo_enhanced_capabilities()
    show_implementation_plan()

    print(f"\n🎯 Key Value Proposition:")
    print("Static Database + Live Documentation + AI Integration")
    print("= Transforms intimidating PDG into approachable workflows")

    print(f"\n✨ For your wife (CGI professional):")
    print("• Familiar SOP concepts → Enhanced with live examples")
    print("• PDG registry entries → Enhanced with workflow tutorials")
    print("• Python functions → Enhanced with working code snippets")
    print("• 'Not a fan of PDG' → 'PDG makes sense now!'")

if __name__ == "__main__":
    asyncio.run(main())

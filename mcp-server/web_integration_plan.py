#!/usr/bin/env python3
"""
Implementation Plan: Integrating Web Search and Fetch into Zabob MCP Server
Step-by-step guide to enhance static database with live documentation
"""

# Step 1: Enhanced server.py with documentation integration
ENHANCED_SERVER_EXAMPLE = '''
# Add these imports to server.py
from typing import Optional

# Enhanced tool implementations:

@mcp.tool("enhanced_search_node_types")
async def enhanced_search_node_types(keyword: str, include_docs: bool = True, limit: int = 5):
    """Search node types with optional live documentation integration."""
    try:
        with db:
            # Get static database results
            node_types = db.search_node_types(keyword, limit)

            result = {
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

            if include_docs and node_types:
                # Enhance top 3 results with live documentation
                enhanced_nodes = []

                for node in node_types[:3]:
                    enhanced_node = result["node_types"][node_types.index(node)].copy()

                    # Use web search to find documentation
                    search_query = f"Houdini {node.name} {node.category} node documentation examples"
                    search_results = await vscode_websearchforcopilot_webSearch(search_query)
                    enhanced_node["documentation_search"] = search_results.get("results", [])[:3]

                    # Try to fetch SideFX official documentation
                    if node.category.lower() in ['sop', 'top', 'object', 'dop']:
                        doc_url = f"https://www.sidefx.com/docs/houdini/nodes/{node.category.lower()}/{node.name}.html"
                        try:
                            doc_content = await fetch_webpage([doc_url], f"{node.name} node documentation")
                            enhanced_node["official_docs"] = {
                                "url": doc_url,
                                "content_preview": doc_content[:400] + "..." if len(doc_content) > 400 else doc_content
                            }
                        except:
                            enhanced_node["official_docs"] = {"url": doc_url, "status": "fetch_failed"}

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

            result = {
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

            if include_examples and functions:
                # Enhance top 3 functions with examples
                enhanced_functions = []

                for func in functions[:3]:
                    enhanced_func = result["functions"][functions.index(func)].copy()

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
                            enhanced_func["hom_docs"] = {
                                "url": doc_url,
                                "content_preview": doc_content[:400] + "..." if len(doc_content) > 400 else doc_content
                            }
                        except:
                            enhanced_func["hom_docs"] = {"url": doc_url, "status": "fetch_failed"}

                    enhanced_functions.append(enhanced_func)

                result["enhanced_results"] = enhanced_functions
                result["enhancement_note"] = "Top results enhanced with code examples and documentation"

            return result

    except Exception as e:
        return {"error": f"Enhanced function search failed: {str(e)}"}


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
                "workflow_query": workflow_description,
                "relevant_pdg_components": [
                    {"name": e.name, "registry": e.registry}
                    for e in unique_entries[:8]
                ],
                "component_count": len(unique_entries)
            }

            # Search for workflow tutorials and guides
            tutorial_query = f"Houdini PDG TOPs {workflow_description} workflow tutorial"
            search_results = await vscode_websearchforcopilot_webSearch(tutorial_query)
            result["workflow_tutorials"] = search_results.get("results", [])[:5]

            # Fetch general PDG documentation for context
            try:
                pdg_doc_url = "https://www.sidefx.com/docs/houdini/tops/index.html"
                pdg_content = await fetch_webpage([pdg_doc_url], "PDG workflow documentation")
                result["pdg_context"] = {
                    "url": pdg_doc_url,
                    "content_preview": pdg_content[:500] + "..." if len(pdg_content) > 500 else pdg_content
                }
            except:
                result["pdg_context"] = {"url": pdg_doc_url, "status": "fetch_failed"}

            # If we found file-related components, get specific file handling docs
            if any("file" in e.name.lower() for e in unique_entries):
                try:
                    file_doc_url = "https://www.sidefx.com/docs/houdini/tops/intro.html#files"
                    file_content = await fetch_webpage([file_doc_url], "PDG file handling documentation")
                    result["file_handling_docs"] = {
                        "url": file_doc_url,
                        "content_preview": file_content[:300] + "..." if len(file_content) > 300 else file_content
                    }
                except:
                    result["file_handling_docs"] = {"url": file_doc_url, "status": "fetch_failed"}

            return result

    except Exception as e:
        return {"error": f"PDG workflow assistance failed: {str(e)}"}


@mcp.tool("get_node_documentation")
async def get_node_documentation(node_name: str, node_category: str = "sop"):
    """Get comprehensive documentation for a specific node."""
    try:
        # First check if node exists in database
        with db:
            matching_nodes = db.search_node_types(node_name, limit=10)
            exact_match = None
            for node in matching_nodes:
                if node.name.lower() == node_name.lower():
                    exact_match = node
                    break

        if not exact_match:
            return {"error": f"Node '{node_name}' not found in database"}

        result = {
            "node_name": exact_match.name,
            "category": exact_match.category,
            "description": exact_match.description,
            "inputs": f"{exact_match.min_inputs}-{exact_match.max_inputs}",
            "outputs": exact_match.max_outputs
        }

        # Fetch official documentation
        doc_url = f"https://www.sidefx.com/docs/houdini/nodes/{exact_match.category.lower()}/{exact_match.name}.html"
        try:
            doc_content = await fetch_webpage([doc_url], f"{exact_match.name} complete documentation")
            result["official_documentation"] = {
                "url": doc_url,
                "content": doc_content
            }
        except:
            result["official_documentation"] = {"url": doc_url, "status": "fetch_failed"}

        # Search for tutorials and examples
        tutorial_query = f"Houdini {exact_match.name} node tutorial examples"
        search_results = await vscode_websearchforcopilot_webSearch(tutorial_query)
        result["tutorials_and_examples"] = search_results.get("results", [])[:5]

        # Search for VEX/Python code examples if it's a SOP
        if exact_match.category.lower() == "sop":
            code_query = f"Houdini {exact_match.name} VEX Python code examples"
            code_search = await vscode_websearchforcopilot_webSearch(code_query)
            result["code_examples"] = code_search.get("results", [])[:3]

        return result

    except Exception as e:
        return {"error": f"Node documentation retrieval failed: {str(e)}"}
'''

def show_implementation_steps():
    """Show the step-by-step implementation process."""
    print("🛠️  Step-by-Step Implementation Plan")
    print("=" * 40)

    steps = [
        {
            "step": "1. Add Web Search Integration",
            "description": "Import and use vscode-websearchforcopilot_webSearch tool",
            "code": """
# In server.py, add:
from typing import Optional

# Use in tools:
search_results = await vscode_websearchforcopilot_webSearch(query)
            """,
            "test": "Search for 'Houdini lattice node examples'"
        },
        {
            "step": "2. Add Fetch Integration",
            "description": "Import and use fetch_webpage tool",
            "code": """
# Use fetch_webpage tool:
doc_content = await fetch_webpage([url], query_description)
            """,
            "test": "Fetch https://www.sidefx.com/docs/houdini/nodes/sop/lattice.html"
        },
        {
            "step": "3. Enhance Existing Tools",
            "description": "Add optional documentation parameters to current tools",
            "changes": [
                "search_node_types → enhanced_search_node_types",
                "search_functions → enhanced_search_functions",
                "Add new pdg_workflow_assistant tool"
            ]
        },
        {
            "step": "4. Update Demo Scripts",
            "description": "Modify demo scripts to showcase enhanced capabilities",
            "changes": [
                "Update quick_demo.py to use enhanced tools",
                "Add documentation integration examples",
                "Show before/after comparisons"
            ]
        },
        {
            "step": "5. Error Handling",
            "description": "Add robust error handling for web operations",
            "considerations": [
                "Handle network failures gracefully",
                "Provide fallback to static data only",
                "Cache frequently accessed documentation"
            ]
        }
    ]

    for i, step in enumerate(steps, 1):
        print(f"\n📋 Step {i}: {step['step']}")
        print("-" * (len(step['step']) + 10))
        print(f"   {step['description']}")

        if 'code' in step:
            print(f"   Code example:")
            print(step['code'])

        if 'test' in step:
            print(f"   Test: {step['test']}")

        if 'changes' in step:
            print(f"   Changes:")
            for change in step['changes']:
                print(f"     • {change}")

        if 'considerations' in step:
            print(f"   Considerations:")
            for consideration in step['considerations']:
                print(f"     • {consideration}")

def show_demo_enhancement_examples():
    """Show specific demo enhancement examples."""
    print(f"\n🎭 Demo Enhancement Examples")
    print("=" * 30)

    examples = [
        {
            "scenario": "SOP Node Discovery",
            "current": "User: 'Find deformation nodes'\nResponse: Lists lattice, wiredeform, twist",
            "enhanced": """User: 'Find deformation nodes with examples'
Response:
• lattice (Sop node) - Deforms geometry using a lattice
  📚 Official docs: [SideFX lattice documentation]
  🎓 Tutorials: ['Lattice deformation tutorial', 'Advanced lattice techniques']
  📖 Live preview: 'The Lattice SOP deforms the input geometry...'"""
        },
        {
            "scenario": "Python Function Help",
            "current": "User: 'Find geometry functions'\nResponse: Lists hou.Geometry.globPrims()",
            "enhanced": """User: 'Find geometry functions with examples'
Response:
• hou.Geometry.globPrims() - Select primitives by pattern
  📚 HOM docs: [Official function documentation]
  💻 Code examples: ['Python geometry selection tutorial', 'globPrims examples']
  📖 Live preview: 'globPrims(pattern) -> tuple of Prim objects...'"""
        },
        {
            "scenario": "PDG Workflow Assistant",
            "current": "User: 'PDG file processing'\nResponse: Lists File dependency, filecompress node",
            "enhanced": """User: 'Help me set up PDG file processing workflow'
Response:
• Relevant components: File (Dependency), filecompress (Node), filecopy (Node)
• Workflow tutorials: ['PDG file processing pipeline', 'Batch file operations']
• PDG context: 'TOP networks process work items through nodes...'
• File handling: 'File dependencies track input/output relationships...'"""
        }
    ]

    for example in examples:
        print(f"\n🎬 {example['scenario']}")
        print("-" * (len(example['scenario']) + 3))
        print("📊 CURRENT:")
        print(f"   {example['current']}")
        print("\n✨ ENHANCED:")
        for line in example['enhanced'].split('\n'):
            print(f"   {line}")

def show_target_audience_impact():
    """Show the impact for the target audience."""
    print(f"\n👩‍🎨 Impact for CGI Professional Learning PDG")
    print("=" * 45)

    print("""
🎯 Current Challenge: "PDG is overwhelming, not a fan"

📊 Static Database Response:
   "Here are PDG components that exist..."

✨ Enhanced Documentation Response:
   "Here are PDG components + how to use them + working examples"

🚀 Transformation:
   Before: Database browser showing what exists
   After:  Learning assistant showing how to succeed

💡 Specific Value for Your Wife:
   • Familiar SOP workflows → Enhanced with live examples
   • Intimidating PDG registry → Enhanced with tutorial workflows
   • Abstract Python functions → Enhanced with working code snippets
   • "Not a fan of PDG" → "PDG makes sense with real examples!"

🎯 Demo Impact:
   Instead of: "The system knows about 131 PDG entries"
   You show: "The system helps you learn PDG workflows step-by-step"
    """)

def main():
    """Run the implementation plan overview."""
    print("🚀 Zabob MCP Server: Web Search & Fetch Integration Plan")
    print("=" * 60)
    print("Transforming static database into live documentation assistant")

    print(f"\n📋 Integration Overview:")
    print("• Add vscode-websearchforcopilot_webSearch integration")
    print("• Add fetch_webpage integration")
    print("• Enhance existing MCP tools with documentation")
    print("• Update demo to showcase live capabilities")

    show_implementation_steps()
    show_demo_enhancement_examples()
    show_target_audience_impact()

    print(f"\n🎯 Next Actions:")
    print("1. Implement enhanced tools in server.py")
    print("2. Test web search and fetch integration")
    print("3. Update demo scripts to showcase enhanced capabilities")
    print("4. Validate with real Houdini documentation URLs")

    print(f"\n✨ Result: Static knowledge + Live docs + AI guidance")
    print("Perfect for making PDG approachable instead of intimidating!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Interactive Demo Script for Zabob MCP Server
Demonstrates real tool calls and responses for a CGI artist learning PDG
"""

import json
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from zabob.mcp.database import HoudiniDatabase

def print_header(title, icon="🎬"):
    """Print a styled header."""
    print(f"\n{icon} {title}")
    print("=" * (len(title) + 3))

def print_section(title, icon="📝"):
    """Print a styled section."""
    print(f"\n{icon} {title}")
    print("-" * (len(title) + 3))

def print_results(data, max_items=5):
    """Pretty print results from MCP tools."""
    if isinstance(data, dict):
        if 'error' in data:
            print(f"❌ Error: {data['error']}")
            return

        # Handle different response formats
        if 'functions' in data:
            print(f"Found {data['count']} functions:")
            for i, func in enumerate(data['functions'][:max_items]):
                print(f"  {i+1}. {func['name']} ({func['module']})")
                if func.get('docstring'):
                    doc = func['docstring'][:100] + "..." if len(func['docstring']) > 100 else func['docstring']
                    print(f"     {doc}")

        elif 'node_types' in data:
            print(f"Found {data['count']} node types:")
            for i, node in enumerate(data['node_types'][:max_items]):
                print(f"  {i+1}. {node['name']} ({node['category']})")
                if node.get('description'):
                    print(f"     {node['description'][:100]}...")

        elif 'entries' in data:
            print(f"Found {data['count']} registry entries:")
            for i, entry in enumerate(data['entries'][:max_items]):
                print(f"  {i+1}. {entry['name']} ({entry['registry']})")

        elif 'modules' in data:
            print(f"Found {data['total_count']} modules (showing {len(data['modules'])}):")
            for i, module in enumerate(data['modules'][:max_items]):
                print(f"  {i+1}. {module['name']} - {module['function_count']} functions ({module['status']})")

        elif 'statistics' in data:
            print("Database Statistics:")
            for key, value in data['statistics'].items():
                print(f"  • {key.replace('_', ' ').title()}: {value:,}")
            print(f"  • Database: {data['database_path']}")

        if data.get('count', 0) > max_items:
            print(f"  ... and {data['count'] - max_items} more")

def demo_scenario(title, description, tool_name, **kwargs):
    """Run a demo scenario."""
    print_section(f"Scenario: {title}")
    print(f"Query: \"{description}\"")
    print(f"Tool: {tool_name}")

    try:
        with HoudiniDatabase() as db:
            # Call the appropriate method
            if tool_name == "get_primitive_functions":
                result = {
                    "functions": [
                        {
                            "name": f.name,
                            "module": f.module,
                            "docstring": f.docstring[:200] + "..." if f.docstring and len(f.docstring) > 200 else f.docstring
                        }
                        for f in db.get_primitive_related_functions()
                    ]
                }
                result["count"] = len(result["functions"])

            elif tool_name == "get_functions_returning_nodes":
                functions = db.get_functions_returning_nodes()
                result = {
                    "functions": [
                        {
                            "name": f.name,
                            "module": f.module,
                            "docstring": f.docstring[:200] + "..." if f.docstring and len(f.docstring) > 200 else f.docstring
                        }
                        for f in functions
                    ],
                    "count": len(functions)
                }

            elif tool_name == "search_node_types":
                keyword = kwargs.get("keyword", "")
                nodes = db.search_node_types(keyword, limit=kwargs.get("limit", 20))
                result = {
                    "node_types": [
                        {
                            "name": nt.name,
                            "category": nt.category,
                            "description": nt.description,
                            "inputs": f"{nt.min_inputs}-{nt.max_inputs}",
                            "outputs": nt.max_outputs,
                            "is_generator": nt.is_generator
                        }
                        for nt in nodes
                    ],
                    "count": len(nodes),
                    "keyword": keyword
                }

            elif tool_name == "get_node_types_by_category":
                category = kwargs.get("category")
                nodes = db.get_node_types_by_category(category)
                result = {
                    "node_types": [
                        {
                            "name": nt.name,
                            "category": nt.category,
                            "description": nt.description,
                            "inputs": f"{nt.min_inputs}-{nt.max_inputs}",
                            "outputs": nt.max_outputs,
                            "is_generator": nt.is_generator
                        }
                        for nt in nodes
                    ],
                    "count": len(nodes),
                    "category": category or "all"
                }

            elif tool_name == "search_pdg_registry":
                keyword = kwargs.get("keyword", "")
                entries = db.search_pdg_registry(keyword, limit=kwargs.get("limit", 50))
                result = {
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

            elif tool_name == "get_pdg_registry":
                registry_type = kwargs.get("registry_type")
                entries = db.get_pdg_registry(registry_type)
                result = {
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

            elif tool_name == "search_functions":
                keyword = kwargs.get("keyword", "")
                functions = db.search_functions_by_keyword(keyword, limit=kwargs.get("limit", 20))
                result = {
                    "functions": [
                        {
                            "name": f.name,
                            "module": f.module,
                            "docstring": f.docstring[:200] + "..." if f.docstring and len(f.docstring) > 200 else f.docstring
                        }
                        for f in functions
                    ],
                    "count": len(functions),
                    "keyword": keyword
                }

            elif tool_name == "get_modules_summary":
                modules = db.get_modules_summary()
                result = {
                    "modules": [
                        {
                            "name": m.name,
                            "status": m.status,
                            "function_count": m.function_count,
                            "file": m.file
                        }
                        for m in modules[:50]
                    ],
                    "total_count": len(modules)
                }

            elif tool_name == "get_database_stats":
                stats = db.get_database_stats()
                result = {
                    "database_path": str(db.db_path),
                    "statistics": stats
                }

            print_results(result)

    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run the complete demo."""
    print_header("Zabob MCP Server Interactive Demo", "🎬")
    print("Demonstrating capabilities for CGI artists learning PDG workflows")
    print("Target: Professional with 40+ years CGI experience, learning Houdini automation")

    # Scenario 1: Familiar territory - geometry operations
    demo_scenario(
        "Geometry Manipulation Basics",
        "What functions are available for working with primitives and geometry?",
        "get_primitive_functions"
    )

    # Scenario 2: Node creation - bridge to automation
    demo_scenario(
        "Building Networks Programmatically",
        "Show me functions that create or return Houdini nodes",
        "get_functions_returning_nodes"
    )

    # Scenario 3: SOP nodes - familiar concepts
    demo_scenario(
        "SOP Node Discovery",
        "What SOP nodes are available for deformation?",
        "search_node_types",
        keyword="deform"
    )

    # Scenario 4: PDG registry - making it approachable
    demo_scenario(
        "PDG File Operations",
        "What PDG components handle file operations?",
        "search_pdg_registry",
        keyword="file"
    )

    # Scenario 5: PDG schedulers
    demo_scenario(
        "PDG Scheduler Options",
        "Show me all available PDG schedulers",
        "get_pdg_registry",
        registry_type="Scheduler"
    )

    # Scenario 6: Attribute scripting
    demo_scenario(
        "Attribute Manipulation",
        "Find functions for working with point and primitive attributes",
        "search_functions",
        keyword="attribute"
    )

    # Scenario 7: TOP nodes for PDG
    demo_scenario(
        "TOP Node Types",
        "What TOP nodes are available for procedural workflows?",
        "get_node_types_by_category",
        category="Top"
    )

    # Scenario 8: Module overview
    demo_scenario(
        "Python Module Landscape",
        "Give me an overview of available Houdini Python modules",
        "get_modules_summary"
    )

    # Scenario 9: System scope
    demo_scenario(
        "Database Statistics",
        "What's the scope of information available?",
        "get_database_stats"
    )

    print_header("Demo Complete! Key Takeaways", "✨")
    print("• Bridges familiar SOP concepts to Python automation")
    print("• Makes PDG registry discoverable and less intimidating")
    print("• Provides instant access to Houdini's vast API")
    print("• Reduces learning curve for procedural pipeline development")
    print("• Comprehensive coverage: 131 PDG entries, 2000+ functions, 500+ nodes")
    print("\n🚀 Ready to accelerate your Houdini Python workflows!")

if __name__ == "__main__":
    main()

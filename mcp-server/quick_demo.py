#!/usr/bin/env python3
"""
Quick Demo: Test Zabob MCP Server Tools
Run this to see live examples of each tool's output
"""

import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def demo_tool(tool_name, description, func, *args, **kwargs):
    """Demo a single tool with error handling."""
    print(f"\n🔧 {tool_name}")
    print(f"   {description}")
    print("-" * 50)

    try:
        result = func(*args, **kwargs)

        if isinstance(result, dict) and 'error' in result:
            print(f"❌ {result['error']}")
        elif isinstance(result, dict):
            # Pretty print based on content
            if 'count' in result:
                print(f"📊 Found {result['count']} results")

            # Show samples
            for key in ['functions', 'node_types', 'entries', 'modules']:
                if key in result:
                    items = result[key][:3]  # Show first 3
                    for i, item in enumerate(items, 1):
                        if key == 'functions':
                            print(f"  {i}. {item['name']} ({item['module']})")
                        elif key == 'node_types':
                            print(f"  {i}. {item['name']} - {item['category']} node")
                        elif key == 'entries':
                            print(f"  {i}. {item['name']} ({item['registry']})")
                        elif key == 'modules':
                            print(f"  {i}. {item['name']} - {item['function_count']} functions")

                    if result['count'] > 3:
                        print(f"  ... and {result['count'] - 3} more")
                    break

            # Show stats if available
            if 'statistics' in result:
                stats = result['statistics']
                print(f"📈 Database contains:")
                print(f"   • {stats.get('functions', 0):,} functions")
                print(f"   • {stats.get('node_types', 0):,} node types")
                print(f"   • {stats.get('pdg_registry_entries', 0):,} PDG registry entries")

        else:
            print(f"✅ {result}")

    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run quick demos of all tools."""
    try:
        from zabob.mcp.database import HoudiniDatabase

        print("🎬 Zabob MCP Server - Quick Tool Demo")
        print("=" * 45)

        db = HoudiniDatabase()
        print(f"📁 Database: {db.db_path}")

        with db:
            # Demo each tool
            demo_tool(
                "get_database_stats",
                "Overview of database contents",
                lambda: {
                    "statistics": db.get_database_stats(),
                    "database_path": str(db.db_path)
                }
            )

            demo_tool(
                "get_primitive_functions",
                "Functions for geometry/primitive operations",
                lambda: {
                    "functions": [
                        {"name": f.name, "module": f.module}
                        for f in db.get_primitive_related_functions()
                    ],
                    "count": len(db.get_primitive_related_functions())
                }
            )

            demo_tool(
                "search_functions",
                "Search for attribute-related functions",
                lambda: {
                    "functions": [
                        {"name": f.name, "module": f.module}
                        for f in db.search_functions_by_keyword("attribute", 5)
                    ],
                    "count": len(db.search_functions_by_keyword("attribute", 5))
                }
            )

            demo_tool(
                "search_node_types",
                "Find deformation SOP nodes",
                lambda: {
                    "node_types": [
                        {"name": nt.name, "category": nt.category}
                        for nt in db.search_node_types("deform", 5)
                    ],
                    "count": len(db.search_node_types("deform", 5))
                }
            )

            demo_tool(
                "get_node_types_by_category",
                "All TOP nodes for PDG workflows",
                lambda: {
                    "node_types": [
                        {"name": nt.name, "category": nt.category}
                        for nt in db.get_node_types_by_category("Top")[:5]
                    ],
                    "count": len(db.get_node_types_by_category("Top"))
                }
            )

            demo_tool(
                "search_pdg_registry",
                "PDG components for file operations",
                lambda: {
                    "entries": [
                        {"name": e.name, "registry": e.registry}
                        for e in db.search_pdg_registry("file", 5)
                    ],
                    "count": len(db.search_pdg_registry("file", 5))
                }
            )

            demo_tool(
                "get_pdg_registry",
                "All PDG schedulers",
                lambda: {
                    "entries": [
                        {"name": e.name, "registry": e.registry}
                        for e in db.get_pdg_registry("Scheduler")
                    ],
                    "count": len(db.get_pdg_registry("Scheduler"))
                }
            )

        print("\n✨ Demo complete!")
        print("🚀 These tools provide AI agents instant access to Houdini's Python API")
        print("💡 Perfect for accelerating PDG learning and automation workflows")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the mcp-server directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

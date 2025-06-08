#!/usr/bin/env python3
"""
Demonstration script showing the capabilities of the enhanced Zabob MCP server.

This script simulates how a user would interact with the Zabob system to get
answers about Houdini modules, functions, and node types.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from zabob.mcp.database import HoudiniDatabase

    async def demo_zabob_capabilities():
        """Demonstrate the key capabilities Bob wanted."""

        print("🎬 Zabob MCP Server Demonstration")
        print("=" * 50)

        db = HoudiniDatabase()
        print(f"📁 Using database: {db.db_path}")

        with db:
            # Scenario 1: "What functions in this module return nodes?"
            print("\n🔍 Scenario 1: Finding functions that return nodes")
            print("-" * 45)

            node_functions = db.get_functions_returning_nodes()
            print(f"Found {len(node_functions)} functions that return node objects:")

            # Group by module for better presentation
            by_module = {}
            for func in node_functions:
                if func.module not in by_module:
                    by_module[func.module] = []
                by_module[func.module].append(func)

            # Show top modules with node-returning functions
            for module, funcs in sorted(by_module.items())[:5]:
                print(f"\n  📦 {module}:")
                for func in funcs[:3]:  # Show first 3 functions per module
                    print(f"     • {func.name}() → {func.datatype}")
                if len(funcs) > 3:
                    print(f"     ... and {len(funcs) - 3} more")

            # Scenario 2: "What module types might help select and operate on a group of primitives?"
            print("\n\n🔍 Scenario 2: Finding primitive selection and operation functions")
            print("-" * 65)

            prim_functions = db.get_primitive_related_functions()
            print(f"Found {len(prim_functions)} primitive-related functions:")

            # Group by module
            prim_by_module = {}
            for func in prim_functions:
                if func.module not in prim_by_module:
                    prim_by_module[func.module] = []
                prim_by_module[func.module].append(func)

            # Show modules most relevant to primitive operations
            for module, funcs in sorted(prim_by_module.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
                print(f"\n  📦 {module} ({len(funcs)} functions):")
                for func in funcs[:4]:  # Show first 4 functions per module
                    print(f"     • {func.name}()")
                if len(funcs) > 4:
                    print(f"     ... and {len(funcs) - 4} more")

            # Scenario 3: Searching for specific functionality
            print("\n\n🔍 Scenario 3: Searching for specific functionality")
            print("-" * 50)

            # Search for geometry manipulation functions
            geo_functions = db.search_functions_by_keyword("geometry", limit=10)
            print(f"Functions related to 'geometry' ({len(geo_functions)} found):")
            for func in geo_functions:
                print(f"     • {func.module}.{func.name}() → {func.datatype}")

            # Scenario 4: Understanding node types for graph analysis
            print("\n\n🔍 Scenario 4: Understanding node types for large graphs")
            print("-" * 55)

            # Show SOP (Surface Operator) nodes - most common in large graphs
            sop_nodes = db.get_node_types_by_category("Sop")
            print(f"SOP (Surface Operator) nodes ({len(sop_nodes)} total):")

            # Show most commonly used node types
            common_sops = [n for n in sop_nodes if n.name in [
                'transform', 'copy', 'merge', 'group', 'delete', 'blast',
                'primitive', 'attribwrangle', 'foreach'
            ]]

            for node in common_sops:
                inputs_str = f"{node.min_inputs}-{node.max_inputs}" if node.min_inputs != node.max_inputs else str(node.min_inputs)
                print(f"     • {node.name}: {node.description[:60]}...")
                print(f"       Inputs: {inputs_str}, Outputs: {node.max_outputs}")

            # Scenario 5: Database overview
            print("\n\n📊 Database Overview")
            print("-" * 20)
            stats = db.get_database_stats()
            for key, value in stats.items():
                print(f"  {key.replace('_', ' ').title()}: {value:,}")

        print("\n" + "=" * 50)
        print("✅ Demonstration complete! Zabob is ready to help users")
        print("   understand complex Houdini workflows and node graphs.")

    # Run the demonstration
    asyncio.run(demo_zabob_capabilities())

except Exception as e:
    print(f"❌ Error running demonstration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

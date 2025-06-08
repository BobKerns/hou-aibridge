#!/usr/bin/env python3
"""
Test script for the Zabob database functionality.
"""

import sys
from pathlib import Path

# Add the paths for zabob modules
ROOT = Path(__file__).parent.parent.parent.parent
CORE_SRC = ROOT / 'zabob-modules/src'
COMMON_SRC = ROOT / 'houdini/zcommon/src'
MCP_SRC = ROOT / 'mcp-server/src'

for p in (CORE_SRC, COMMON_SRC, MCP_SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from zabob.mcp.database import HoudiniDatabase

    print("Testing Zabob database functionality...")

    # Initialize database
    db = HoudiniDatabase()
    print(f"Database path: {db.db_path}")

    # Test database stats
    with db:
        stats = db.get_database_stats()
        print("\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Test function search
        print("\nSearching for 'node' functions...")
        node_functions = db.search_functions_by_keyword("node", limit=5)
        for func in node_functions:
            print(f"  {func.module}.{func.name} -> {func.datatype}")

        # Test functions returning nodes
        print("\nFunctions returning nodes...")
        returning_nodes = db.get_functions_returning_nodes()
        print(f"Found {len(returning_nodes)} functions that return nodes")
        for func in returning_nodes[:5]:  # Show first 5
            print(f"  {func.module}.{func.name} -> {func.datatype}")

        # Test primitive functions
        print("\nPrimitive-related functions...")
        prim_functions = db.get_primitive_related_functions()
        print(f"Found {len(prim_functions)} primitive-related functions")
        for func in prim_functions[:5]:  # Show first 5
            print(f"  {func.module}.{func.name}")

    print("\n✅ Database test completed successfully!")

except Exception as e:
    print(f"❌ Error testing database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

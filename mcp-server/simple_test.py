#!/usr/bin/env python3
"""Simple test for the MCP server database functionality."""

import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from zabob.mcp.database import HoudiniDatabase

    print("🧪 Testing Zabob MCP Database...")

    # Test database connection
    db = HoudiniDatabase()
    print(f"✅ Database found: {db.db_path}")

    # Test database stats
    with db:
        stats = db.get_database_stats()
        print("📊 Database Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value:,}")

        # Quick test of functions returning nodes
        node_functions = db.get_functions_returning_nodes()
        print(f"\n🔧 Functions returning nodes: {len(node_functions)}")

        if node_functions:
            print("   Sample functions:")
            for func in node_functions[:3]:
                print(f"     • {func.module}.{func.name} → {func.datatype}")

        # Quick test of primitive functions
        prim_functions = db.get_primitive_related_functions()
        print(f"\n📐 Primitive-related functions: {len(prim_functions)}")

        if prim_functions:
            print("   Sample functions:")
            for func in prim_functions[:3]:
                print(f"     • {func.module}.{func.name}")

        print("\n✅ All tests passed! Database is ready for MCP server.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

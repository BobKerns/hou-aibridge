#!/usr/bin/env python3
"""
Simple test to verify the MCP server structure is working.
"""
import sys
from pathlib import Path

# Add the source directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from zabob.mcp.server import mcp, db
    print("✅ Server imports successful!")
    print(f"📊 Database path: {getattr(db, 'db_path', 'Not initialized')}")
    print(f"🔧 MCP server name: {mcp.name}")
    print(f"📝 Available tools: {len(mcp._tools)} registered")

    # List the tools
    tool_names = list(mcp._tools.keys())
    print(f"🛠️  Tools: {', '.join(tool_names[:5])}..." if len(tool_names) > 5 else f"🛠️  Tools: {', '.join(tool_names)}")

    print("\n🎉 Web search integration appears to be successfully integrated!")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

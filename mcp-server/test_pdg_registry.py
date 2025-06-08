#!/usr/bin/env python3
"""Test the new PDG registry functionality."""

import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from zabob.mcp.database import HoudiniDatabase

    print("🧪 Testing PDG Registry functionality...")

    # Test database connection
    db = HoudiniDatabase()
    print(f"✅ Database found: {db.db_path}")

    with db:
        # Test get all PDG registry entries
        all_entries = db.get_pdg_registry()
        print(f"\n📊 Total PDG registry entries: {len(all_entries)}")

        # Show sample entries
        if all_entries:
            print("   Sample entries:")
            for entry in all_entries[:5]:
                print(f"     • {entry.name} ({entry.registry})")

        # Test filtering by registry type
        node_entries = db.get_pdg_registry("Node")
        print(f"\n🔧 Node registry entries: {len(node_entries)}")

        scheduler_entries = db.get_pdg_registry("Scheduler")
        print(f"📅 Scheduler registry entries: {len(scheduler_entries)}")

        service_entries = db.get_pdg_registry("Service")
        print(f"🔧 Service registry entries: {len(service_entries)}")

        # Test search functionality
        search_results = db.search_pdg_registry("file", limit=5)
        print(f"\n🔍 Search results for 'file': {len(search_results)}")
        if search_results:
            for entry in search_results:
                print(f"     • {entry.name} ({entry.registry})")

        print("\n✅ All PDG registry tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

#!/usr/bin/env python3
"""
Test script to verify the new database schema after regeneration.

This will test that the type fields are now plain strings instead of JSON.
"""

import sqlite3
import sys
from pathlib import Path

# Add the paths for zabob modules
ROOT = Path(__file__).parent.parent.parent.parent.parent
CORE_SRC = ROOT / 'zabob-modules/src'
COMMON_SRC = ROOT / 'houdini/zcommon/src'

for p in (CORE_SRC, COMMON_SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from zabob.core.paths import ZABOB_OUT_DIR

def test_new_schema():
    """Test the new database schema."""
    db_path = ZABOB_OUT_DIR / "20.5.584" / "houdini_data_dev.db"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False

    print(f"🗄️  Testing database: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Test 1: Check that type field contains plain strings, not JSON
        print("\n1. Testing type field format...")
        cursor.execute("SELECT type FROM houdini_module_data WHERE name = 'hou' LIMIT 1")
        row = cursor.fetchone()
        if row:
            type_value = row['type']
            print(f"   Type value: {repr(type_value)}")
            if type_value.startswith('"') and type_value.endswith('"'):
                print("   ❌ Still using JSON format (quoted strings)")
                return False
            else:
                print("   ✅ Using plain string format")

        # Test 2: Check that boolean fields are proper integers/booleans
        print("\n2. Testing boolean field format...")
        cursor.execute("SELECT isGenerator FROM houdini_node_types LIMIT 1")
        row = cursor.fetchone()
        if row:
            bool_value = row['isGenerator']
            print(f"   Boolean value: {repr(bool_value)} (type: {type(bool_value)})")
            if isinstance(bool_value, str) and bool_value in ('"true"', '"false"'):
                print("   ❌ Still using JSON format for booleans")
                return False
            else:
                print("   ✅ Using proper boolean format")

        # Test 3: Count functions with plain type values
        print("\n3. Testing function queries...")
        cursor.execute("SELECT COUNT(*) FROM houdini_module_data WHERE type = 'function'")
        function_count = cursor.fetchone()[0]
        print(f"   Functions found: {function_count}")

        # Test 4: Check a few sample entries
        print("\n4. Testing sample function entries...")
        cursor.execute("""
            SELECT name, type, datatype, parent_name
            FROM houdini_module_data
            WHERE type = 'function'
            LIMIT 5
        """)

        for row in cursor.fetchall():
            print(f"   Function: {row['name']} (type: {repr(row['type'])}, datatype: {repr(row['datatype'])})")

        # Test 5: Test node types with proper categories
        print("\n5. Testing node type categories...")
        cursor.execute("SELECT DISTINCT category FROM houdini_node_types ORDER BY category LIMIT 10")
        categories = [row['category'] for row in cursor.fetchall()]
        print(f"   Categories found: {categories}")

        if any(cat.startswith('"') and cat.endswith('"') for cat in categories):
            print("   ❌ Categories still using JSON format")
            return False
        else:
            print("   ✅ Categories using plain string format")

        print("\n🎉 All tests passed! Database schema is correctly fixed.")
        return True

if __name__ == "__main__":
    success = test_new_schema()
    sys.exit(0 if success else 1)

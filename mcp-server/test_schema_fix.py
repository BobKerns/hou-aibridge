#!/usr/bin/env python3
"""
Test script to verify the schema fix for EntryType and builtins.type fields.
"""
import sys
from pathlib import Path

# Add the paths for zabob modules
ROOT = Path(__file__).parent.parent
CORE_SRC = ROOT / 'zabob-modules/src'
COMMON_SRC = ROOT / 'houdini/zcommon/src'

for p in (CORE_SRC, COMMON_SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from zabob.common.analysis_types import HoudiniStaticData, EntryType
from zabob.common.analysis_db import tables
import builtins

def test_schema_fix():
    """Test that EntryType and builtins.type are handled correctly."""
    print("Testing schema fix for EntryType and builtins.type...")

    # Get the table descriptor for HoudiniStaticData
    table_desc = tables[HoudiniStaticData]

    # Check the field mappings
    field_map = table_desc.field_map

    # Test the 'type' field (EntryType)
    type_field = field_map['type']
    print(f"Type field spec:")
    print(f"  - name: {type_field.name}")
    print(f"  - db_type: {type_field.db_type}")
    print(f"  - py_type: {type_field.py_type}")
    print(f"  - is_json: {type_field.is_json}")
    print(f"  - declared_type: {type_field.declared_type}")

    # Test the 'datatype' field (builtins.type)
    datatype_field = field_map['datatype']
    print(f"\nDatatype field spec:")
    print(f"  - name: {datatype_field.name}")
    print(f"  - db_type: {datatype_field.db_type}")
    print(f"  - py_type: {datatype_field.py_type}")
    print(f"  - is_json: {datatype_field.is_json}")
    print(f"  - declared_type: {datatype_field.declared_type}")

    # Check the DDL statement
    print(f"\nDDL statement:")
    print(table_desc.ddl)

    # Check the INSERT statement
    print(f"\nINSERT statement:")
    print(table_desc.insert_stmt)

    # Test value coercion
    test_data = HoudiniStaticData(
        name="test_function",
        type=EntryType.FUNCTION,
        datatype=str,
        docstring="Test function",
        parent_name="test_module",
        parent_type="module"
    )

    print(f"\nTesting value coercion:")
    print(f"Original values:")
    print(f"  - type: {test_data.type!r} (type: {type(test_data.type)})")
    print(f"  - datatype: {test_data.datatype!r} (type: {type(test_data.datatype)})")

    db_values = table_desc.db_values(test_data)
    print(f"\nCoerced values for DB:")
    for i, field in enumerate(table_desc.fields):
        print(f"  - {field.name}: {db_values[i]!r} (type: {type(db_values[i])})")

    # Verify expectations
    assert type_field.db_type == "TEXT", f"Expected TEXT, got {type_field.db_type}"
    assert type_field.py_type == EntryType, f"Expected EntryType, got {type_field.py_type}"
    assert not type_field.is_json, f"Expected is_json=False, got {type_field.is_json}"

    assert datatype_field.db_type == "TEXT", f"Expected TEXT, got {datatype_field.db_type}"
    assert datatype_field.py_type == type, f"Expected type, got {datatype_field.py_type}"
    assert not datatype_field.is_json, f"Expected is_json=False, got {datatype_field.is_json}"

    # Check that INSERT statement doesn't use json() for these fields
    assert "json(?)" not in table_desc.insert_stmt or table_desc.insert_stmt.count("json(?)") < len(table_desc.fields), \
        "All fields are using json(?), fix didn't work"

    print(f"\n✅ Schema fix test passed!")

if __name__ == "__main__":
    test_schema_fix()

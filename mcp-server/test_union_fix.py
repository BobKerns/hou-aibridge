#!/usr/bin/env python3
"""Test script to verify Union type detection for JSON serialization."""

import sys
from pathlib import Path

# Add the zcommon src to the Python path
zcommon_src = Path(__file__).parent.parent / "houdini/zcommon/src"
sys.path.insert(0, str(zcommon_src))

from typing import get_origin, get_args
from zabob.common.analysis_table import AnalysisTableDescriptor
from zabob.common.analysis_types import ParmTemplateInfo, ModuleData
from zabob.common.common_types import JsonData

def test_union_detection():
    """Test that Union types containing container types are detected as needing JSON serialization."""

    # Create table descriptor for ParmTemplateInfo
    table = AnalysisTableDescriptor(ParmTemplateInfo, table_name='test_parm_templates')

    # Get the field info for defaultValue
    field_info = table.field_map.get('defaultValue')

    print(f"Field: defaultValue")
    print(f"  declared_type: {field_info.declared_type}")
    print(f"  py_type: {field_info.py_type}")
    print(f"  db_type: {field_info.db_type}")
    print(f"  is_json: {field_info.is_json}")
    print(f"  nullable: {field_info.nullable}")

    # Test the specific Union type: list['JsonData'] | dict[str, 'JsonData'] | str | int | float | bool | None
    test_type = field_info.declared_type
    print(f"\nAnalyzing Union type: {test_type}")

    # Check if it's a Union
    origin = get_origin(test_type)
    print(f"  Origin: {origin}")

    if hasattr(origin, '__name__') and 'Union' in origin.__name__:
        args = get_args(test_type)
        print(f"  Union args: {args}")

        for i, arg in enumerate(args):
            requires_json = table._requires_json_serialization(arg)
            arg_origin = get_origin(arg)
            print(f"    Arg {i}: {arg} (origin: {arg_origin}) -> requires_json: {requires_json}")

    # Test with a tuple to see if conversion works
    print(f"\nTesting tuple conversion:")
    test_tuple = (0, 22050)
    print(f"  Input: {test_tuple} (type: {type(test_tuple)})")

    try:
        result = field_info.coerce(test_tuple)
        print(f"  Result: {result} (type: {type(result)})")
        print("  SUCCESS: Conversion worked!")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  FAILED: Conversion failed")

if __name__ == "__main__":
    test_union_detection()

def test_module_data_schema():
    """Test ModuleData schema generation to check the status field."""

    # Create table descriptor for ModuleData
    table = AnalysisTableDescriptor(ModuleData, table_name='test_modules')

    print(f"\n" + "="*50)
    print("TESTING ModuleData Schema")
    print("="*50)

    # Get the field info for status
    status_field = table.field_map.get('status')

    print(f"Field: status")
    print(f"  declared_type: {status_field.declared_type}")
    print(f"  py_type: {status_field.py_type}")
    print(f"  db_type: {status_field.db_type}")
    print(f"  is_json: {status_field.is_json}")
    print(f"  nullable: {status_field.nullable}")

    # Print the DDL to see the schema
    print(f"\nGenerated DDL:")
    print(table.ddl)

    # Test with None status (should be allowed)
    print(f"\nTesting None status conversion:")
    try:
        result = status_field.coerce(None)
        print(f"  Input: None -> Result: {result!r}")
        print("  SUCCESS: None conversion worked!")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  FAILED: None conversion failed")

if __name__ == "__main__":
    test_union_detection()
    test_module_data_schema()

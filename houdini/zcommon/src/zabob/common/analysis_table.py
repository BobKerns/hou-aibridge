'''
Specify analysis tables via dataclasses
'''

from dataclasses import dataclass, fields, is_dataclass, MISSING
from typing import get_type_hints, get_origin, get_args, Union, List, Tuple, Type, Any
import inspect
import enum

def dataclass_to_sqlite_table(
    cls: Type,
    table_name: str = None,
    primary_key: List[str] = None,
    foreign_keys: List[Tuple[List[str], str, List[str]]] = None,
    strict: bool = True
) -> str:
    """
    Generate SQLite DDL statement from a dataclass.

    Args:
        cls: The dataclass to convert to a table
        table_name: Custom table name (default: class name)
        primary_key: List of field names to use as primary key (default: first field)
        foreign_keys: List of foreign key constraints as tuples (local_columns, foreign_table, foreign_columns)
        strict: Whether to add STRICT to the table definition

    Returns:
        SQLite DDL CREATE TABLE statement as a string
    """
    # Check if cls is a dataclass
    if not is_dataclass(cls):
        raise TypeError(f"{cls.__name__} is not a dataclass")

    # Get table name
    if table_name is None:
        table_name = cls.__name__

    # Get field definitions
    field_defs = []
    type_hints = get_type_hints(cls)

    # Process fields
    for field in fields(cls):
        field_name = field.name
        field_type = type_hints[field_name]

        # Check if type is Optional/Union with None
        is_optional = False
        origin = get_origin(field_type)

        # Handle Union with None (Optional[X])
        if origin is Union:
            args = get_args(field_type)
            if type(None) in args:
                is_optional = True
                # Find the non-None type
                non_none_types = [arg for arg in args if arg is not type(None)]
                if len(non_none_types) == 1:
                    field_type = non_none_types[0]
                else:
                    # Multiple non-None types - default to TEXT
                    field_type = str

        # Map Python type to SQLite type
        try:
            if field_type is int or field_type is bool or (inspect.isclass(field_type) and issubclass(field_type, enum.IntEnum)):
                sqlite_type = "INTEGER"
            elif field_type is float:
                sqlite_type = "REAL"
            else:
                sqlite_type = "TEXT"
        except TypeError:
            # If type comparison fails (e.g., with generics), default to TEXT
            sqlite_type = "TEXT"

        # Build field definition
        field_def = f"    {field_name} {sqlite_type}"

        # Add NULL constraint
        if not is_optional:
            field_def += " NOT NULL"
        else:
            field_def += " DEFAULT NULL"

        field_defs.append(field_def)

    # Handle primary key
    if not primary_key:
        # Default to first field
        primary_key = [fields(cls)[0].name]

    # Add primary key constraint
    pk_constraint = f"    PRIMARY KEY ({', '.join(primary_key)}) ON CONFLICT REPLACE"

    # Handle foreign keys
    fk_constraints = []
    if foreign_keys:
        for local_cols, foreign_table, foreign_cols in foreign_keys:
            fk_constraint = f"    FOREIGN KEY ({', '.join(local_cols)}) REFERENCES {foreign_table}({', '.join(foreign_cols)})"
            fk_constraints.append(fk_constraint)

    # Combine all constraints
    all_constraints = [pk_constraint] + (fk_constraints if fk_constraints else [])

    # Build the final SQL
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    sql += ",\n".join(field_defs)
    if all_constraints:
        sql += ",\n" + ",\n".join(all_constraints)
    sql += "\n)"
    if strict:
        sql += " STRICT"

    return sql


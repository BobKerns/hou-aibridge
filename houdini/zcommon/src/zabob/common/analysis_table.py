'''
Specify analysis tables via dataclasses
'''

from dataclasses import dataclass, fields, is_dataclass, MISSING
from typing import get_type_hints, get_origin, get_args, Union, List, Tuple, Type, Any
import inspect
import enum

def dataclass_to_sqlite_ddl(
    cls: type,
    primary_key: tuple[str, ...] | None = None,
    foreign_keys: dict[str, tuple[str, str]] | None = None
) -> str:
    """
    Convert a dataclass to a SQLite CREATE TABLE DDL statement.

    Args:
        cls: The dataclass type
        primary_key: Tuple of field names to use as primary key. If None, uses first field.
        foreign_keys: Dict mapping field names to (table, column) tuples for foreign key constraints

    Returns:
        SQLite CREATE TABLE statement
    """
    if not is_dataclass(cls):
        raise ValueError(f"{cls} is not a dataclass")

    table_name = cls.__name__.lower()
    dataclass_fields = fields(cls)

    if not dataclass_fields:
        raise ValueError(f"{cls} has no fields")

    # Default primary key is first field
    if primary_key is None:
        primary_key = (dataclass_fields[0].name,)

    # Type mapping
    def map_type(field_type) -> tuple[str, bool]:
        """Map Python type to SQLite type and nullable flag."""
        origin = get_origin(field_type)

        # Check if it's Optional (Union with None)
        if origin is Union:
            args = get_args(field_type)
            if type(None) in args:
                # It's Optional, get the non-None type
                actual_type = next(t for t in args if t is not type(None))
                sql_type, _ = map_type(actual_type)
                return sql_type, True

        # Map basic types
        if field_type in (int, bool):
            return "INTEGER", False
        elif field_type is float:
            return "REAL", False
        elif field_type is str:
            return "TEXT", False
        else:
            # Default to TEXT for unknown types
            return "TEXT", False

    # Build column definitions
    columns = []
    for field in dataclass_fields:
        sql_type, nullable = map_type(field.type)
        col_def = f"{field.name} {sql_type}"

        if nullable:
            col_def += " DEFAULT NULL"
        else:
            col_def += " NOT NULL"

        columns.append(col_def)

    # Build CREATE TABLE statement
    ddl = f"CREATE TABLE {table_name} (\n"
    ddl += ",\n".join(f"    {col}" for col in columns)

    # Add primary key constraint
    if primary_key:
        ddl += f",\n    PRIMARY KEY ({', '.join(primary_key)}) ON CONFLICT REPLACE"

    # Add foreign key constraints
    if foreign_keys:
        for field_name, (ref_table, ref_column) in foreign_keys.items():
            ddl += f",\n    FOREIGN KEY ({field_name}) REFERENCES {ref_table}({ref_column})"

    ddl += "\n);"

    return ddl

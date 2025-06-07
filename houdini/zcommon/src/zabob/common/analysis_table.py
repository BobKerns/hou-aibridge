'''
Specify analysis tables via dataclasses
'''

from collections.abc import Collection, Container, Sequence, Mapping
from dataclasses import Field, fields, is_dataclass
from functools import cache
from typing import Generic, get_origin, get_args, TypeAlias, TypeVar, Any, Union
from types import UnionType, GenericAlias
from pathlib import Path
import json

from zabob.common.common_types import (
    JsonData, JsonAtomic, JsonAtomicNonNull, JsonArray, JsonObject,
    JsonDataNonNull
)
from zabob.common.analysis_types import AnalysisDBItem
from zabob.common.common_utils import value, none_or, get_name

D = TypeVar('D', bound=AnalysisDBItem)

ForeignKeyConstraint: TypeAlias = tuple[tuple[str, ...], str, tuple[str, ...]]

'''
Foreign key constraint definition for analysis tables.
It is a tuple of the form:
    (local_names, ref_table, ref_columns)
'''

class AnalysisTableDescriptor(Generic[D]):
    """
    Descriptor for analysis tables defined as dataclasses.
    Provides a method to convert the dataclass to a SQLite
    CREATE TABLE DDL statement, including support for primary keys
    and foreign keys.

    Provides method to create SQLite INSERT statements from
    dataclass classes.

    Provides a method to coerce values in the dataclass instances
    to the correct types for SQLite, given the value and field name.
    This should operate on a pre-built map of field names to conversions.
    Fields of type str, int, float, bool, and their union types with None
    need no conversion, but other types need to convert to str, or str|None.
    The function none_or(<value>, converter) should be used to convert
    fields that include None, where <value> is the value to convert
    and converter is a function that converts the value to a string.

    If the type of field offers a name, via name attribute or method,
    or a __name__ attribute, it should be used to convert the value
    to a string, otherwise the value should be converted to a string
    using str(value). The exception is Path types, which should
    convert to a string using str(value).
    """

    __table_name: str
    @property
    def table_name(self) -> str:
        """Get the name of the analysis table."""
        return self.__table_name

    __dataclass: type[D]
    @property
    def dataclass(self) -> type[D]:
        """Get the dataclass type of the analysis table."""
        return self.__dataclass

    __primary_key: tuple[str, ...]
    @property
    def primary_key(self) -> tuple[str, ...]:
        """Get the primary key fields of the analysis table."""
        return self.__primary_key

    __foreign_keys: tuple[ForeignKeyConstraint, ...]
    @property
    def foreign_keys(self) -> tuple[ForeignKeyConstraint, ...]:
        """Get the foreign key constraints of the analysis table."""
        return self.__foreign_keys

    def __init__(self,
                 dataclass: type[D], /, *,
                 table_name: str = "",
                 primary_key: tuple[str, ...] = (),
                 foreign_keys: tuple[ForeignKeyConstraint, ...] = ()):
        if not is_dataclass(dataclass):
            raise ValueError(f"{dataclass} is not a dataclass")
        self.__table_name = table_name or dataclass.__name__.lower()
        self.__dataclass = dataclass
        if not primary_key:
            # Default to the first field as primary key if none specified
            primary_key = (fields(dataclass)[0].name,)
        self.__primary_key = primary_key
        self.__foreign_keys = foreign_keys

    def _map_type(self, field_type: type|UnionType|GenericAlias|str) -> tuple[str, bool]:
        """Map Python type to SQLite type and nullable flag."""
        origin = get_origin(field_type)

        # Check if it's Optional (Union with None)
        if origin is UnionType:
            args = get_args(field_type)
            if type(None) in args:
                # It's Optional, get the non-None type
                actual_type = next(t for t in args if t is not type(None))
                sql_type, _ =self. _map_type(actual_type)
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


    def _field_to_column_def(self, field: Field) -> str:
        """Convert a dataclass field to a SQLite column definition."""
        sql_type, nullable = self._map_type(field.type)
        col_def = f"{field.name} {sql_type}"

        if nullable:
            col_def += " DEFAULT NULL"
        else:
            col_def += " NOT NULL"

        return col_def

    @property
    @cache
    def ddl(
        self,
    ) -> str:
        """
        Convert a dataclass to a SQLite CREATE TABLE DDL statement.

        Returns:
            SQLite CREATE TABLE statement
        """
        dataclass_fields = fields(class_or_instance=self.dataclass)

        if not dataclass_fields:
            raise ValueError(f"{self.dataclass} has no fields")

        # Build CREATE TABLE statement
        return "\n".join((
            f"CREATE TABLE IF NOT EXISTS {self.table_name} (",
            ",\n".join((
                    *(
                        f"    {col}"
                        for field in dataclass_fields
                        for col in value(self._field_to_column_def(field))
                    ),
                    f"    PRIMARY KEY ({', '.join(self.primary_key)}) ON CONFLICT REPLACE",
                    *(f"    FOREIGN KEY ({field_expr}) REFERENCES {ref_table}({ref_expr})"
                        for field_names, ref_table, ref_column in self.foreign_keys
                        for field_expr in value(", ".join(field_names))
                        for ref_expr in value(", ".join(ref_column))
                        ),
                )),
            ") STRICT;"
        ))

    def _coerce_value(self, field_name: str, val: Any) -> Any:
        """
        Coerce a value to the correct type for SQLite based on the field type.

        Args:
            field_name: The name of the field
            val: The value to coerce

        Returns:
            The coerced value ready for SQLite
        """
        # Find the field's type
        field = next((f for f in fields(self.dataclass) if f.name == field_name), None)
        if not field:
            raise ValueError(f"Field {field_name} not found in {self.dataclass.__name__}")

        field_type = field.type
        # Handle 3.12+ type statements.
        field_type = getattr(field_type, '__value__', field_type)
        origin = get_origin(field_type)

        # Handle Union/Optional types
        if origin is UnionType:
            args = get_args(field_type)
            if type(None) in args:
                # Get the non-None type
                if field_type in (JsonData, JsonAtomic, JsonArray, JsonObject, Any|None):
                    return
                else:
                    # Remove None from the Union. If only one remains, the Union will be simplified.
                    # to the single type.
                    actual_type = Union[*(t for t in args if t is not type(None))]
                if val is None:
                    return None
                return none_or(val, lambda v: self._convert_single_type(actual_type, v))
            elif field_type in (JsonDataNonNull, JsonAtomicNonNull, Any):
                field_type = JsonDataNonNull
        if origin in (list, tuple, dict, set, Sequence, Mapping, Container, Collection):
            return self._convert_single_type(JsonData, val)
        return self._convert_single_type(field_type, val)

    def _convert_single_type(self, type_hint: Any, val: Any) -> Any:
        """Convert a single value based on its type."""
        # Primitive types that need no conversion
        if type_hint in (int, float, bool):
            return val

        if type_hint is str:
            if isinstance(val, str):
                return val
            return get_name(val)
        if type_hint == JsonData:
            if val is None:
                return None
            return json.dumps(val)
        if type_hint == JsonDataNonNull:
            if val is None:
                raise ValueError("JsonDataNonNull cannot be None")
            return json.dumps(val)
        # Path types
        if (isinstance(val, Path)
            or ((hasattr(type_hint, "__origin__")
                 and get_origin(type_hint) is Path))):
            return str(val)

        # Other types we are treating as named objects.
        return get_name(val)

    @property
    @cache
    def insert_stmt(self) -> str:
        """
        Create a SQL INSERT statement template for the dataclass.

        Returns:
            A parameterized SQL INSERT statement
        """

        field_names = [
            field.name
            for field in fields(self.dataclass)
        ]
        columns = ', '.join(field_names)
        placeholders = ", ".join("?" for _ in field_names)

        return f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

    def db_values(self, instance: D) -> list[Any]:
        """
        Get the coerced values from a dataclass instance for SQL insertion.

        Args:
            instance: An instance of the dataclass

        Returns:
            A list of coerced values ready for SQL insertion
        """
        if not isinstance(instance, self.dataclass):
            raise ValueError(f"Expected instance of {self.dataclass.__name__}, got {type(instance).__name__}")

        return [
            self._coerce_value(field.name, getattr(instance, field.name))
            for field in fields(self.dataclass)
        ]

    def insert(self, cursor, instance: D) -> None:
        """
        Insert a dataclass instance into the SQLite database.

        Args:
            cursor: A SQLite cursor for executing the query
            instance: An instance of the dataclass to insert
        """
        values = self.db_values(instance)
        cursor.execute(self.insert_stmt, values)


'''
Specify analysis tables via dataclasses
'''

from collections.abc import Callable
from dataclasses import Field, fields, is_dataclass
from functools import cache
from typing import Generic, NamedTuple, get_origin, get_args, TypeAlias, TypeVar, Any, Union, Literal
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

TypeExpression: TypeAlias = str|type|UnionType|GenericAlias|type[UnionType]

class AnalysisFieldSpec(NamedTuple):
    name: str
    py_type: TypeExpression
    db_type: str
    declared_type: TypeExpression
    is_json: bool
    nullable: bool
    coerce: Callable[[Any], Any]

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

    __fields: tuple[AnalysisFieldSpec, ...]
    @property
    @cache
    def fields(self) -> tuple[AnalysisFieldSpec, ...]:
        """Get the field specifications of the analysis table."""
        return tuple(self._field_info(field)
                     for field in fields(self.dataclass))

    @property
    @cache
    def field_map(self) -> dict[str, AnalysisFieldSpec]:
        """
        Get a mapping of field names to their specifications.
        This is used to quickly access field information by name.
        """
        return {field.name: field for field in self.fields}

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

    def _map_type(self,
                  field_type: TypeExpression,
                  ) -> tuple[str, TypeExpression, bool]:
        """Map Python type to SQLite type and nullable flag."""
        origin = get_origin(field_type)

        # Check if it's Optional (Union with None)
        if origin is UnionType:
            args = get_args(field_type)
            if type(None) in args:
                # It's Optional, get the non-None type
                actual_type = Union[*(t for t in args if t is not type(None))]
                sql_type, actual_type, _ =self. _map_type(actual_type)
                return sql_type, actual_type, True
            if is_jsonable(field_type):
                return "TEXT", JsonData, False
        if is_jsonable(field_type):
            return "TEXT", JsonData, False
        actual_type = (
            origin
            or getattr(field_type, '__value__', None)  # Handle GenericAlias
            or field_type
        )
        # Map basic types
        if actual_type in (int, bool):
            return "INTEGER", actual_type, False
        elif actual_type is float:
            return "REAL", actual_type, False
        elif actual_type is str:
            return "TEXT", actual_type, False
        elif actual_type in (JsonAtomic, JsonAtomicNonNull, JsonData, JsonDataNonNull,
                            JsonArray, JsonObject, dict, list, tuple):
            # jsonb is not supported in older sqlite versions (including the one shipped
            # with MacOS), so we use TEXT for JSON data.) jsonb needs 3.45+.
            #return "BLOB", JsonData, True
            return "TEXT", JsonData, True
        else:
            # Default to TEXT for unknown types
            return "TEXT", actual_type, False

    def _field_info(self, field: Field) -> AnalysisFieldSpec:
        """
        Get the field information for a dataclass field.

        Args:
            field: The dataclass field

        Returns:
            An AnalysisFieldSpec with the field name, SQLite type, nullable flag,
            and a conversion function
        """
        sql_type, actual_type, nullable = self._map_type(field.type)
        return AnalysisFieldSpec(
            name=field.name,
            db_type=sql_type,
            py_type=actual_type,
            declared_type=field.type,
            is_json=actual_type in (JsonData, JsonDataNonNull, JsonAtomic, JsonAtomicNonNull, JsonArray, JsonObject,
                                    dict, list, tuple),
            nullable=nullable,
            coerce=self._converter(actual_type, nullable)
        )

    def _converter(self, actual_type: TypeExpression, nullable: bool) -> Callable[[Any], Any]:
        """
        Get a conversion function for a single type.
        This is used to convert values to the correct type for SQLite.
        """
        if nullable:
            # If the type is nullable, we need to handle None values
            if actual_type is type(None):
                return lambda x: None
            converter = self._converter(actual_type, False)
            def nullable_converter(val: Any) -> Any:
                if val is None:
                    return None
                return converter(val)
            return nullable_converter
        # Primitive types that need no conversion
        if actual_type in (int, float, bool):
            return actual_type

        if actual_type is str:
            return get_name
        if actual_type in (JsonData, JsonDataNonNull):
            return json_converter
        # Path types
        if actual_type in (Path, Path|None):
            return str
        # Other types we are treating as named objects.
        return get_name

    def _field_to_column_def(self, field: Field) -> str:
        """Convert a dataclass field to a SQLite column definition."""
        sql_type, _, nullable = self._map_type(field.type)
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
        field_info = self.field_map.get(field_name)
        if field_info is None:
            raise ValueError(f"Field {field_name} not found in {self.dataclass.__name__}")
        return field_info.coerce(val)

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
        columns = ', '.join(field.name for field in self.fields)
        placeholders = ", ".join("json(?)" if field.is_json else '?'
                                                for field in self.fields)

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

def json_converter(obj: JsonObject) -> str:
    """
    Convert an object to a JSON string for SQLite storage.
    Handles Path objects and other serializable types.
    """
    return json.dumps(obj, cls=JsonDataEncoder)

class JsonDataEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling AnalysisDBItem dataclasses.

    This is responsible for converting objects we may find in python
    data structures to JSON-serializable types. For example, it
    converts tuples, sets, and frozensets to lists, and Path objects
    and types to their string representations.

    It will be used to serialize data that that is declared as a
    JsonData type or similar, identified as a JSON field, but runtime
    data may not conform to the declared type.

    To a limited extent, we allow declarations of types we know
    can be converted to JSON. This helps with type compatibility;
    for example, we can declare a field as list[Path] and it will
    be serialized as a list of strings. The `AnalysisTableDescriptor`
    class is responsible for recognizing such types. This class handles
    conversion of those types and more to JSON, for example, a `Path`
    encountered at any level of the data structure will be converted.
    """
    def default(self, o: Any) -> Any:
        match o:
            case tuple()|set()|frozenset():  # Fixed syntax error with missing parenthesis
                return list(o)
            case Path():
                return str(o)
            case int()|str()|float()|bool()|list()|dict() :
                return super().default(o)  # Fallback to default serialization
        return get_name(o)

def is_jsonable(ft: TypeExpression):
    """
    Check if a type expression is JSON serializable.
    This checks if the type is a basic type, a Literal, or a Union of basic types.
    The basic types include int, float, bool, str, list, dict, tuple,
    and any type that we convert to JSON (see `JsonDataEncoder`).

    None has already been removed from the Union type. This is just confirming
    that the resulting union type is JSON serializable.

    This is not a general check for JSON serializability, nor a type analysis.
    The goal is to enable use of types specifically for the table definition classes,
    that are used to define the analysis tables. To allow for good type checking,
    a subset of types is used that are known to be JSON serializable
    and can be used in the analysis tables as JSON data. This is part of the process
    of recognizing those fields, to pass to the database as JSON data.

    It is only relevant at the top level during defining the analysis tables.

    Args:
        ft: The type expression to check
    Returns:
        bool: True if the type is JSON serializable, False otherwise
    """
    return all(t is Literal or issubclass(t,  (
        int, float, bool, str, list, dict, tuple, frozenset,
        Path, type, GenericAlias, UnionType))
            for t in (get_origin(a)
                    for a in get_args(ft))
                       if t is not None)

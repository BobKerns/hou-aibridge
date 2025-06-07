'''
Specify analysis tables via dataclasses
'''

from dataclasses import Field, fields, is_dataclass
from typing import Generic, get_origin, get_args, TypeAlias, TypeVar
from types import UnionType, GenericAlias

from zabob.common import AnalysisDBItem
from zabob.common.common_utils import value

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

    def __init__(self, dataclass: type[D], primary_key: tuple[str, ...] = ()
                 , foreign_keys: tuple[ForeignKeyConstraint, ...] = ()):
        if not is_dataclass(dataclass):
            raise ValueError(f"{dataclass} is not a dataclass")
        self.__table_name = dataclass.__name__.lower()
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
            f"CREATE TABLE {self.table_name} (",
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


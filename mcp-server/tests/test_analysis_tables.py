'''
Unit tests for analysis_table module
'''

import pytest
from dataclasses import dataclass, field, fields
from zabob.common.analysis_table import map_type, field_to_column_def, dataclass_to_sqlite_ddl


class TestMapType:
    """Test the map_type function."""

    def test_int_type(self):
        sql_type, nullable = map_type(int)
        assert sql_type == "INTEGER"
        assert nullable is False

    def test_bool_type(self):
        sql_type, nullable = map_type(bool)
        assert sql_type == "INTEGER"
        assert nullable is False

    def test_float_type(self):
        sql_type, nullable = map_type(float)
        assert sql_type == "REAL"
        assert nullable is False

    def test_str_type(self):
        sql_type, nullable = map_type(str)
        assert sql_type == "TEXT"
        assert nullable is False

    def test_optional_int(self):
        sql_type, nullable = map_type(int|None)
        assert sql_type == "INTEGER"
        assert nullable is True

    def test_optional_str(self):
        sql_type, nullable = map_type(str|None)
        assert sql_type == "TEXT"
        assert nullable is True

    def test_union_with_none(self):
        sql_type, nullable = map_type(float|None)
        assert sql_type == "REAL"
        assert nullable is True

    def test_unknown_type(self):
        sql_type, nullable = map_type(list)
        assert sql_type == "TEXT"
        assert nullable is False


class TestFieldToColumnDef:
    """Test the field_to_column_def function."""

    def test_required_int_field(self):
        @dataclass
        class Test:
            id: int

        field = fields(Test)[0]
        col_def = field_to_column_def(field)
        assert col_def == "id INTEGER NOT NULL"

    def test_optional_str_field(self):
        @dataclass
        class Test:
            name: str|None

        field = fields(Test)[0]
        col_def = field_to_column_def(field)
        assert col_def == "name TEXT DEFAULT NULL"

    def test_required_float_field(self):
        @dataclass
        class Test:
            score: float

        field = fields(Test)[0]
        col_def = field_to_column_def(field)
        assert col_def == "score REAL NOT NULL"


class TestDataclassToSqliteDDL:
    """Test the dataclass_to_sqlite_ddl function."""

    def test_simple_dataclass(self):
        @dataclass
        class User:
            id: int
            name: str
            email: str

        ddl = dataclass_to_sqlite_ddl(User)
        expected = """CREATE TABLE user (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    PRIMARY KEY (id) ON CONFLICT REPLACE
);"""
        assert ddl == expected

    def test_dataclass_with_optional_fields(self):
        @dataclass
        class Product:
            id: int
            name: str
            description: str|None
            price: float
            discount: float|None = field(default=None)

        ddl = dataclass_to_sqlite_ddl(Product)
        expected = """CREATE TABLE product (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT NULL,
    price REAL NOT NULL,
    discount REAL DEFAULT NULL,
    PRIMARY KEY (id) ON CONFLICT REPLACE
);"""
        assert ddl == expected

    def test_custom_primary_key(self):
        @dataclass
        class OrderItem:
            order_id: int
            product_id: int
            quantity: int

        ddl = dataclass_to_sqlite_ddl(OrderItem, primary_key=("order_id", "product_id"))
        expected = """CREATE TABLE orderitem (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id) ON CONFLICT REPLACE
);"""
        assert ddl == expected

    def test_foreign_keys(self):
        @dataclass
        class Post:
            id: int
            user_id: int
            title: str

        ddl = dataclass_to_sqlite_ddl(
            Post,
            foreign_keys={"user_id": ("user", "id")}
        )
        expected = """CREATE TABLE post (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    PRIMARY KEY (id) ON CONFLICT REPLACE,
    FOREIGN KEY (user_id) REFERENCES user(id)
);"""
        assert ddl == expected

    def test_multiple_foreign_keys(self):
        @dataclass
        class Comment:
            id: int
            post_id: int
            user_id: int
            content: str

        ddl = dataclass_to_sqlite_ddl(
            Comment,
            foreign_keys={
                "post_id": ("post", "id"),
                "user_id": ("user", "id")
            }
        )
        assert "FOREIGN KEY (post_id) REFERENCES post(id)" in ddl
        assert "FOREIGN KEY (user_id) REFERENCES user(id)" in ddl

    def test_no_primary_key_specified(self):
        @dataclass
        class Simple:
            field1: str
            field2: int

        ddl = dataclass_to_sqlite_ddl(Simple, primary_key=None)
        # Should use first field as primary key
        assert "PRIMARY KEY (field1) ON CONFLICT REPLACE" in ddl

    def test_not_a_dataclass_raises_error(self):
        class NotADataclass:
            pass

        with pytest.raises(ValueError, match="is not a dataclass"):
            dataclass_to_sqlite_ddl(NotADataclass)

    def test_empty_dataclass_raises_error(self):
        @dataclass
        class Empty:
            pass

        with pytest.raises(ValueError, match="has no fields"):
            dataclass_to_sqlite_ddl(Empty)

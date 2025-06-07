'''
Definition and access for the analysis database.
'''

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from collections.abc import Generator
import sys
from typing import IO

from zabob.common.analysis_types import (
    AnalysisDBItem, AnalysisDBWriter, HoudiniStaticData, ModuleData,
    NodeCategoryInfo, NodeTypeInfo, ParmTemplateInfo,
)
from zabob.common.common_utils import (
    T, VERBOSE, Condition, get_name, none_or, trace as _trace,
)
from zabob.common.timer import timer
from zabob.common.analysis_table import AnalysisTableDescriptor

tables: dict[type, AnalysisTableDescriptor] = {
    table.dataclass: table
    for table in (
        AnalysisTableDescriptor[ModuleData](
            ModuleData,
            table_name='houdini_modules',
            primary_key=('name',),
        ),
        AnalysisTableDescriptor[HoudiniStaticData](
            HoudiniStaticData,
            table_name='houdini_module_data',
            primary_key=('name', 'type'),
            foreign_keys=(
                (
                    ('parent_name', 'parent_type'),
                    'houdini_module_data',
                    ('name', 'type'),
                ),
            ),
        ),
        AnalysisTableDescriptor[NodeCategoryInfo](
            NodeCategoryInfo,
            table_name='houdini_categories',
            primary_key=('name',),
        ),
        AnalysisTableDescriptor[NodeTypeInfo](
            NodeTypeInfo,
            table_name='houdini_node_types',
            primary_key=('name', 'category'),
            foreign_keys=(
                (
                    ('category',),
                    'houdini_categories',
                    ('name',),
                ),
            ),
        ),
        AnalysisTableDescriptor[ParmTemplateInfo](
            ParmTemplateInfo,
            table_name='houdini_parm_templates',
            primary_key=('node_type_name', 'node_type_category', 'name'),
            foreign_keys=(
                (
                    ('node_type_name', 'node_type_category'),
                    'houdini_node_types',
                    ('name', 'category'),
                ),
            )
        ),
    )
}


@contextmanager
def analysis_db(db_path: Path|None=None,
                connection: sqlite3.Connection|None=None,
                write: bool=False,
                ) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for accessing the analysis database. If supplied
    with an existing connection, it will use that connection, and the
    caller is responsible for closing it.

    If a database path is provided, and `write=True` is supplied,
    it will create and initialize the database at that path if it
    does not exist. If `write=False`, it will open the database
    without initializing it, allowing access to existing data.

    In either case, the database must exist if `write=False`, and will
    close it when the context manager exits.

    If neither is provided, it raises a `ValueError`.

    Args:
        db_path (Path): The path to the SQLite database file.
        connection (sqlite3.Connection): An existing SQLite connection to use.
        write (bool): If True, the database will be opened in write mode and initialized.

    Yields:
        sqlite3.Connection: A connection to the SQLite database.
    """
    def init_db(conn: sqlite3.Connection):
        """
        Initialize the database with the required schema.
        This function should be called after creating a new database file.
        """
        if write:
            print('Initializing tables...')
            for table in tables.values():
                conn.execute(table.ddl)
            # Write-Aahead Logging (WAL) mode permits concurrent reads and writes,
            # which is useful for long-running operations like this.
            # It also allows the database to be accessed by multiple processes, so
            # long as they are on the same machine.
            conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA mmap_size=268435456;")  # 256 MB
    match db_path, connection:
        case None, None:
            raise ValueError("Either db_path or connection must be provided")
        case _, sqlite3.Connection():
            # If a connection is provided, whoever opened is responsible for
            #closing it.
            init_db(connection)
            yield connection
            return
        case Path(), _:
            db_path = db_path.resolve()
            if not db_path.exists():
                if write:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    raise FileNotFoundError(f"Database file {db_path} does not exist")
            with sqlite3.connect(db_path) as conn:
                init_db(conn)
                yield conn


@contextmanager
def analysis_db_writer(db_path: Path|None=None,
                       connection: sqlite3.Connection|None=None,
                       trace: Condition=False,
                       label: str|None=None,
                       file: IO[str]=sys.stderr,
                       ) -> Generator[AnalysisDBWriter, None, None]:
    """
    Context manager for writing to the analysis database.
    If an existing connection is provided, it will use that connection,
    and the caller is responsible for closing it.

    If a database path is provided, it will create and initialize the
    database at that path if it does not exist.
    If neither is provided, it raises a `ValueError`.

    Args:
        db_path (Path): The path to the SQLite database file.
        connection (sqlite3.Connection): An existing SQLite connection to use.
        trace (Condition): If `True`, `None`, or a `Callable`,
            trace the items being written.
        label (str|None): A label for the trace output.

    Yields:
        AnalysisDBWriter: A callable that writes items to the analysis database.
    """
    # Insert or update static data
    item_count = 0
    cur_module: ModuleData|None = None
    with analysis_db(db_path=db_path, connection=connection, write=True) as conn:
        """
        Context manager for writing to the analysis database.
        Args:
            conn (sqlite3.Connection): The SQLite connection to use.
        Yields:
            AnalysisDBWriter: A callable that writes items to the analysis database.
            """

        with timer('Storing') as progress:
            cursor = conn.cursor()
            item_count = 0
            cur_module = None
            def writer(datum: T, /) -> T|AnalysisDBItem:
                nonlocal item_count, cur_module
                _trace(datum, condition=trace, label=f'{label}.writer', file=file)
                table = tables.get(type(datum))
                if table is None:
                    return datum

                match datum:
                    case ModuleData():
                        if cur_module is not None:
                            # Commit the previous module data
                            cursor.execute('''
                                UPDATE houdini_modules
                                SET count = ?, status = ?, reason = ?
                                WHERE name = ?
                            ''', (
                                item_count,
                                'OK',
                                None,
                                cur_module.name))

                        conn.commit()
                        status = datum.status
                        if isinstance(status, Exception):
                            t = type(status)
                            if hasattr(t, '__name__'):
                                status = t.__name__
                            else:
                                status = str(t)
                        table.insert(cursor, datum)
                        item_count = 0
                        if datum.status is not None:
                            if VERBOSE:
                                progress(f'Skipping module {datum.name} due to status: {datum.status}: {datum.reason}')
                            return datum
                        if VERBOSE:
                            progress(f'Processing module {datum.name}...')
                        cur_module = datum
                        conn.commit()
                        return datum
                    case HoudiniStaticData():
                        item_count += 1
                        if item_count % 100 == 0:
                            conn.commit()

                        if datum.parent_name is not None:
                            #print(f'Processing {datum.type} {datum.name} with parent {datum.parent_name}...')
                            #if str(name) == 'BlendShape' or name == 'hou' or datum.type == EntryType.OBJECT:
                            #    breakpoint()
                            table.insert(cursor, datum)
                        else:
                            #print(f'Processing {datum.type} {datum.name} without parent...')
                            cursor.execute('PRAGMA foreign_keys = OFF;')
                            conn.commit()
                            # Change line number
                            cursor.execute('''
                                INSERT OR REPLACE INTO houdini_module_data (name, type, datatype, docstring, parent_name, parent_type)
                                VALUES (?, ?, ?, ?, NULL, NULL)
                            ''', (datum.name,
                                    get_name(datum.type),
                                    get_name(datum.datatype),
                                    datum.docstring))
                            cursor.execute('PRAGMA foreign_keys = ON;')
                            conn.commit()
                        return datum
                    case _:
                        table.insert(cursor, datum)
                        return datum

            yield writer


def get_stored_modules(db_path: Path|None=None,
                       connection: sqlite3.Connection|None=None,
                       successful: bool = True,
                       failed: bool = False,
                       ) -> Generator[str, None, None]:
    """
    Get names of modules already stored in the database.

    Args:
        db_path (Path): Path to the SQLite database file.
        conn (sqlite3.Connection|None): An existing SQLite connection, if available.
        successful (bool): If True, include modules successfully loaded.
        failed (bool): If True, include modules not successfully loaded.

    Yields:
        str: Name of each module stored in the database.
    """
    with analysis_db(db_path=db_path, connection=connection) as conn:
        """
        Retrieve stored module names from the database.
        Args:
            conn (sqlite3.Connection): The SQLite connection to use.
        Yields:
            str: Name of each module stored in the database.
        """

        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='houdini_modules'
            """)

            if not cursor.fetchone():
                return

            # Query module names
            if successful:
                cursor.execute("SELECT name FROM houdini_modules where status = 'OK'")
                for row in cursor.fetchall():
                    yield row[0]
            if failed:
                cursor.execute("SELECT name FROM houdini_modules where status <> 'OK'")
                for row in cursor.fetchall():
                    yield row[0]
        except sqlite3.Error as e:
            print(f"Error retrieving stored modules: {e}", file=sys.stderr)

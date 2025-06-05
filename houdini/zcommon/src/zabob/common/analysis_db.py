'''
Definition and access for the analysis database.
'''

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
import sqlite3
from pathlib import Path
from collections.abc import Generator
import sys
from typing import IO

from zabob.common.analysis_types import AnalysisDBItem, AnalysisDBWriter, HoudiniStaticData, ModuleData
from zabob.common.common_utils import T, get_name, none_or
from zabob.common.timer import timer


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
            conn.execute('PRAGMA foreign_keys = ON;')
            # Create tables if they doesn't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS houdini_module_data (
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    datatype TEXT NOT NULL,
                    docstring TEXT,
                    parent_name TEXT DEFAULT NULL,
                    parent_type TEXT DEFAULT NULL,
                    PRIMARY KEY (name, type) ON CONFLICT REPLACE,
                    FOREIGN KEY (parent_name, parent_type) REFERENCES houdini_module_data(name, type)
                ) STRICT
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS houdini_modules (
                    name TEXT NOT NULL PRIMARY KEY,
                    directory TEXT DEFAULT NULL,
                    file TEXT DEFAULT NULL,
                    count INTEGER DEFAULT NULL,
                    status TEXT DEFAULT NULL,
                    reason TEXT DEFAULT NULL
                ) STRICT
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS houdini_categories (
                    name TEXT NOT NULL PRIMARY KEY
                ) STRICT
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS houdini_node_types (
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    docstring TEXT DEFAULT NULL,
                    PRIMARY KEY (name, category) ON CONFLICT REPLACE,
                    FOREIGN KEY (category) REFERENCES houdini_categories(name)
                ) STRICT
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS houdini_node_type_params (
                    node_type_name TEXT NOT NULL,
                    node_type_category TEXT NOT NULL,
                    param_name TEXT NOT NULL,
                    param_type TEXT NOT NULL,
                    param_label TEXT DEFAULT NULL,
                    param_default TEXT DEFAULT NULL,
                    param_docstring TEXT DEFAULT NULL,
                    PRIMARY KEY (node_type_name, node_type_category, param_name) ON CONFLICT REPLACE,
                    FOREIGN KEY (node_type_name, node_type_category)
                        REFERENCES houdini_node_types(name, category)
                ) STRICT
            ''')
            # Write-Aahead Logging (WAL) mode permits concurrent reads and writes,
            # which is useful for long-running operations like this.
            # It also allows the database to be accessed by multiple processes, so
            # long as they are on the same machine.
            conn.execute("PRAGMA journal_mode=WAL;")
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
            def writer(datum: T, /) -> Generator[T|AnalysisDBItem, None, None]:
                nonlocal item_count, cur_module
                _trace(datum, condition=trace, label=f'{label}.writer', file=file)
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
                        cursor.execute('''
                            INSERT OR REPLACE INTO houdini_modules (name, directory, file, count, status, reason)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                                datum.name,
                                none_or(datum.directory, str),
                                none_or(datum.file, str),
                                datum.count,
                                status,
                                datum.reason))
                        item_count = 0
                        if datum.status is not None:
                            progress(f'Skipping module {datum.name} due to status: {datum.status}: {datum.reason}')
                            yield datum
                            return
                        progress(f'Processing module {datum.name}...')
                        yield datum
                        cur_module = datum
                        conn.commit()
                    case HoudiniStaticData():
                        item_count += 1
                        if item_count % 100 == 0:
                            conn.commit()

                        if datum.parent_name is not None:
                            #print(f'Processing {datum.type} {datum.name} with parent {datum.parent_name}...')
                            #if str(name) == 'BlendShape' or name == 'hou' or datum.type == EntryType.OBJECT:
                            #    breakpoint()
                            cursor.execute('''
                                INSERT OR REPLACE INTO houdini_module_data (name, type, datatype, docstring,
                                                                            parent_name, parent_type)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                datum.name,
                                get_name(datum.type),
                                get_name(datum.datatype),
                                datum.docstring,
                                datum.parent_name, get_name(datum.parent_type)))
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
                        yield datum
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

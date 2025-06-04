'''
Definition and access for the analysis database.
'''

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from collections.abc import Generator

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

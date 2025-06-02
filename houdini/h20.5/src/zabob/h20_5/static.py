'''
Routines to extract static data from Houdini 20.5.
'''

from pathlib import Path
import sys

import click

import hou

from zabob.common import (
    ZABOB_OUT_DIR,
    import_or_warn, save_static_data_to_db, modules_in_path,
)


IGNORE_MODULES: frozenset[str] = frozenset[str]((
    'unittest.__main__', 'opcode_sum', 'perfmon_sum', 'searchbox',
    'generateHDAToolsForOTL', 'test.autotest', 'test.tf_inherit_check',
    'test._test_embed_structseq', 'plumbum.lib',
))


default_db = ZABOB_OUT_DIR / hou.applicationVersionString() / 'houdini_static_data.db'
@click.command()
@click.argument('db', type=click.Path(exists=False, dir_okay=False, path_type=Path), default=default_db)
def load_data(db: Path=default_db):
    """
    Main function to save Houdini static data to a database.
    Args:
        db (Path): The path to the SQLite database file.
    """
    db.parent.mkdir(parents=True, exist_ok=True)
    save_static_data_to_db(db_path=db,
                           include=modules_in_path(sys.path, IGNORE_MODULES),
                           ignore=IGNORE_MODULES)
    print(f"Static data saved to {db}")

if __name__ == "__main__":
    load_data()

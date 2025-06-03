'''
Routines to extract static data from Houdini 20.5.
'''

from collections.abc import Mapping
from pathlib import Path
import sys
from types import MappingProxyType
from webbrowser import get

import click

import hou

from zabob.common import (
    ZABOB_OUT_DIR,
    save_static_data_to_db, modules_in_path, get_stored_modules,
)


IGNORE_MODULES: Mapping[str, str] = MappingProxyType({
    'opnode_sum': "A script, not a module",
    'perfmon_sum': "A script, not a module.",
    "pycparser._build_tables": "A script that writes files.",
    **{k: "Crashes hython 20.5"
       for k in (
                'dashbox.ui', 'dashbox.textedit', 'dashbox.common', 'dashbox',
                'generateHDAToolsForOTL', 'test.autotest', 'test.tf_inherit_check',
                'test._test_embed_structseq', 'idlelib.idle', 'ocio.editor',
                'hrecipes.models', 'hrecipes.manager', 'pdgd.datalayerserver',
                'assettools', 'searchbox',
                'searchbox.panetabs', 'searchbox.paths', 'searchbox.ui',
                'searchbox.categories', 'searchbox.parms', 'searchbox.tools',
                'searchbox.preferences', 'searchbox.hotkeys', 'searchbox.common',
                'searchbox.viewport_settings', 'searchbox.solaris', 'searchbox.radialmenus',
                'searchbox.help', 'searchbox.expression', 'layout.view', 'layout.assetgallery',
                'layout.panel', 'layout.brushpanel', 'stagemanager.panel',
                'shibokensupport.signature.parser',
            )
       }
    })


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
                           include=modules_in_path(sys.path,
                                                   ignore=IGNORE_MODULES,
                                                   done=get_stored_modules(db)),
                           ignore=IGNORE_MODULES,
                           )
    print(f"Static data saved to {db}")



if __name__ == "__main__":
    load_data()

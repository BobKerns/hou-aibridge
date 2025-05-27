'''
Routines to extract static data from Houdini 20.5.
'''

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from inspect import (
    getdoc, getmembers, isclass, isfunction, ismethod, ismodule,
    ismethoddescriptor, isdatadescriptor,
)
from pathlib import Path
import sys
import os
from typing import Any
from importlib import import_module

import sqlite3

import hou

@contextmanager
def environ(**kwargs: str):
    """
    Context manager to temporarily set environment variables.
    Args:
        **kwargs: Environment variables to set.
    Yields:
        None
    """
    old_environ = dict(os.environ)
    os.environ.update(kwargs)
    try:
        yield os.environ
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


def import_or_warn(module_name: str):
    """
    Import a module and warn if it fails.
    Args:
        module_name (str): The name of the module to import.
    Returns:
        module: The imported module, or None if the import failed.
    """
    try:
        with environ(HOUDINI_ENABLE_HOM_EXTENSIONS='1',):
            print(f"Importing {module_name}...")
            yield import_module(module_name)
    except Exception as e:
        print(f"Warning: Failed to import {module_name}: {e}", file=sys.stderr)


MODULES = [
    loaded_module
    for m in (
        'hou', 'pdg', 'hrpyc', 'soptoolutils', 'canvaseventtypes',
        'viewerstate', 'viewerstate.utils', '_alembic_hom_extensions',
        'pxr', 'husd', 'husd.objtranslator', 'husd.backgroundrenderer',
        'nodegraphview', 'nodegraphdisplay',
        'OpenGL', 'OpenGL.GL', 'OpenGL.GLU', 'OpenGL.GLUT', 'OpenGL.AGL',
        'MaterialX', 'coloraide', 'imageio', 'mercantile', 'PIL',
        'PyOpenColorIO', 'autorig', 'bakeanimation', 'baseinfowindow',
        'bvhviewer', 'channelwranglesnippet', 'charactertoolutils',
        'choptoolutils', 'clonecontrol',
        #'cloud',
        'cloudEULA',
        #'cloudsubmit',
        'cloudtoolutils',
        # 'colorschemeutils',
        # 'contextoptions',
        'cop2toolutils', 'coptoolutils', 'crowds',
        'crowdstoolutils', 'curveutils', 'defaultstatetools', 'defaulttoolmenu',
        'defaulttools', 'digitalassetsupport', 'displaymessage',
        'dopclothproxy', 'dopclothtoolutils', 'dopfemtoolutils',
        'dopgeofiltertoolutils', 'dopinstance', 'dopparticlefluidtoolutils',
        'doppoptoolutils', 'doppyrotoolutils', 'doprbdtoolutils',
        'dopsmoketoolutils', 'dopsparsepyrotools', 'dopstatictoolutils',
        'doptoolutils', 'dopwiretoolutils', 'dragdroputils', 'drivertoolutils',
        'edit', 'expression_functions', 'expressionmenu',
        'fbxexportpreset', 'fileutils', 'furtoolutils',
        'gasresizedynamic',
        # 'generateHDAToolsForOTL', # EXITS!
        'groom', 'groomingradial', 'halo', 'handleutils', 'hdefereval',
        # 'hjsonrpc',
        'hotkeys', 'hotkeys_prototype', 'houcportion',
        'houdiniengineutils', 'houdinihelp', 'houdiniinternals',
        'houdiniInterpreter', 'houxmlrpc', 'hqrop', 'hscp',
        'husd', 'husdui', 'husktrace', 'hutil', 'hwebserver', 'images2gif',
        'inlinecpp', 'insertionpointutils', 'introspect',
        'karma_stats', 'keymaputils', 'landmarking', 'layout',
        'lightlinker',  'lightmixer', 'lightstate', 'logviewer',
        'lopcamutils', 'lopcamandlightutils', 'lopshaderutils',
        'loptoolutils', 'loputils', 'lpetags', 'materiallinker',
        'metaexpr', 'modelview', 'mssbuild', 'mtlx2hda', 'mtlx2karma',
        'muscletoolutils', 'mvexportutils',
        # 'nodegraph',
        # 'nodegraphalign',
        # 'nodegraphautoscroll',
        #'nodegraphbase',
        # 'nodegraphconnect',
        # 'nodegraphdisplay',
        # 'nodegraphdispopts',
        # 'nodegraphedittext',
        # 'nodegraphfastfind',
        'nodegraphflags',
        # 'nodegraphfurutils',
        # 'nodegraphgestures',
        # 'nodegraphhotkeys',
        # 'nodegraphlayout',
        # 'nodegraphpalettes',
        # 'nodegraphpopmenus',
        'nodegraphprefs',
        # 'nodegraphquicknav',
        'nodegraphradialmenu',
        # 'nodegraphsearch',
        # 'nodegraphstates',
        'nodegraphrename',
        # 'nodegraphselectpos',
        # 'nodegraphselecthooks',
        # 'nodegraphsnap',
        # 'nodegraphtitle',
        # 'nodegraphoptui',
        # 'nodegraphutils',
        # 'nodegraphvellumutils',
        # 'nodegraphview',
        'nodesearch', 'nodeselectionutil', 'nodethemes', 'nodeutils',
        'objecttoolutils', 'ocio',
        # 'opnode_sum', # Script, not module.

        # 'package',
        'packfoldermenu', 'parmutils', 'parsepeakuserlog',
        'particletoolutils', 'pdgd', 'pdgdatalayer', 'pdgjob',
        # 'pdgpathmap',
        'pdgservicepanel',
        # 'ppdgstateserver',
        'pdgutils',
        # 'perfmon_sum', # Script, not module.
        'pluginutils', 'poselib', 'posespacedeform', 'pyro2',
        'pythonscriptmenu', 'quickplanes', 'radialmenu', 'recipetoolutils',
        'renderstats', 'rendertracker',
        # 'resourceui',
        'resourceutils',
        'rigtoolutils', 'rmands', 'roptoolutils', 'roputils',
        'sas', 'scenegraphdetails', 'scenegraphlayers',
        'sceneviewerhooks',
        # 'searchbox',
        'shaderhda',
        'shadingutils', 'shelfutils', 'shopclerks',
        'shoptoolutils', 'simtracker', 'skytoolutils',
        'snippetmenu', 'soptoolutils', 'soputils',
        'stagemanager', 'statehud', 'stateutils',
        'stroketoolutils',
        # 'taskgraphtable',
        # 'taskgraphtablepanel',
        'terraintoolutils', 'tilefx', 'toolprompts',
        'toolutils', 'top', 'topnettoolutils', 'toptoolutils',
        'toputils', 'uiutils', 'usdinlinelayermenu',
        'usdprimicons', 'usdrenderers', 'usdroputils',
        'vexpressionmenu', 'viewerhandle', 'viewerstate',
        'volumetoolutils', 'vop2mtlx', 'vopcallbacks',
        'vopfxmenu', 'vopnettoolutils', 'voptoolutils',
        'webapiclient', 'bookish.stores', 'bookish.compat',
        'bookish.text.textify', 'bookish.avenue.avenue',
        'bookish.wiki.pipeline', 'bookish.wiki.includes',
        'bookish.wiki.wikipages', 'bookish.wiki.styles',
        'bookish.avenue.patterns',
    )
    for loaded_module in import_or_warn(m)
]

IGNORE_MODULES: set[str] = {
    'sys', 'os', 'itertools', 'time', 'xml', 'xmlrpc', 'json',
    're', 'subprocess', 'threading', 'multiprocessing', 'queue',
    'logging', 'warnings', 'contextlib', 'functools', 'collections',
    'collections.abc', 'itertools', 'operator', 'shutil', 'pathlib',
    'concurrent', 'concurrent.futures', 'asyncio',
    'socket', 'http', 'urllib',
    'json.decoder', 'json.encoder', 'json.scanner', 'typing',
    'sysconfig', 'importlib', 'importlib.util', 'builtins',
    'math', 'random', 'statistics', 'functools', 'select',
    'zlib', 'gzip', 'bz2', 'lzma', 'base64', 'hashlib',
    'pickle', 'copy', 'copyreg', 'marshal', 'struct',
    'array', 'weakref', 'types', 'codecs', 'encodings',
    'inspect', 'traceback', 'pprint', 'cProfile', 'profile',
    'timeit', 'cgitb', 'faulthandler', 'linecache', 'gc',
    'io', 'numbers', 'shlex', 'heapq', 'ast', 'abc', 'datetime',
    'csv', 'locale', 'fnmatch', 'glob', 'quopri', 'lxml.etree',
    'email', 'email.charset', 'email.errors', 'email.encoders',
    'contextvars', 'reprlib', 'signal', 'ssl', 'errno', 'html',
    'mimetypes', 'genericpath', 'posixpath', 'stat', 'platform',
    'binascii', 'resourceutils', 'future.standard_library',
    'concurrent.futures', 'ctypes', 'ctypes.util', 'ctypes.wintypes',
    'ctypes.macholib', 'ctypes.macholib.dyld', 'ctypes.macholib.framework',
    'bisect', 'numpy', 'scipy', 'matplotlib', 'pandas',
    'scikit-learn', 'sklearn', 'tensorflow', 'torch', 'torchvision',
    'keras', 'tempfile', 'zipfile', 'tarfile', 'gzip', 'bz2',
    'zipimport', 'pkgutil', 'PySide2.support', 'atexit', 'fcntl',
    'lxml', 'markupsafe', 'string', 'mmap', 'posix',  'pwd', 'pyexpat',
    'readline', 'resource', 'shiboken2', 'keyword', 'simplejson',
    'decimal', 'termios', 'unicodedata', 'uuid', 'getpass', 'requests',
    'code', 'poster', 'bookish', 'flask', 'click', 'werkzeug',
    'dataclasses', 'textwrap', 'difflib', 'hnac', 'secrets', 'selectors',
    'jinja2', 'tokenize', 'pydoc', 'configparser', 'html.parser',
    'PySide2.QtWidgets', 'bookish.paths', 'bookish.search', 'urllib.parse',
    'ipaddress', 'calendar', 'bookish.wiki.langpaths', 'bookish.util',
    'jinja2.environment', 'jinja2.nodes', 'socketserver', 'codeop',
    'hutil.Qt.QtWidgets', 'enum', 'pytz', 'xmlrpc.client',
    'xml.parsers.expat', 'future', 'argparse', 'six',
    'bookish.functions', 'bookish.store', 'QtCompat',
}

@dataclass
class HoudiniStaticData:
    """
    A class to represent static data extracted from Houdini 20.5.

    Attributes:
        scene_file (str): The path to the current Houdini scene file.
        project_directory (str): The current project directory.
        houdini_version (str): The version of Houdini being used.
        user_name (str): The name of the user running Houdini.
    """
    name: str
    type: str
    datatype: str
    docstring: str|None = None
    houdini_version: str = field(default_factory=lambda: hou.applicationVersionString())
    parent_name: str|None = None
    parent_type: str|None = None

def get_members_safe(obj: Any):
    """
    Safely get members of an object, excluding private members.
    Args:
        obj (Any): The object to get members from.
    yields:
        tuple[str, Any]: A tuple containing the name and member of the object.
    """
    try:
        yield from getmembers(obj)
    except Exception as e:
        print(f"Warning: Failed to get members of {obj}: {e}", file=sys.stderr)
        # Fallback to an empty list if getmembers fails
        yield from []



def get_static_module_data():
    """
    Extract static data from Houdini 20.5 regarding modules, classes, functions, and constants
    etc. exposed by the hou module.

    This function traverses the hou module and its submodules, collecting information
    about each item, including its name, type, data type, docstring, Houdini version,
    and parent information if applicable.

    Yields:
        HoudiniStaticData: An instance of HoudiniStaticData for each item found in the hou module.
    The data includes:


    Returns:
        dict: A dictionary containing the static data.
    """
    seen = set()
    houdini_version = hou.applicationVersionString()
    moduleClass = type(hou)
    builtin_function_or_method = type(hou.applicationVersion)
    def dtype(v):
        name = type(v).__name__
        if 'tuple' in name or 'Tuple' in name:
            return 'tuple'
        return name
    def docstring(v):
        """
        Get the docstring of a Houdini object, excluding the parent class docstring if it matches.
        Args:
            v (Any): The Houdini object to get the docstring for.
        Returns:
            str|None: The docstring of the object, or None if it is the same as the parent class docstring.
        """
        own = getdoc(v)
        if own is None:
            return None
        parent = getdoc(type(v))
        if own == parent:
            return None
        return getdoc(v) or None

    def ishouenumtype(v):
        """
        Check if the given value is a Houdini enum type.
        Args:
            v (Any): The value to check.
        Returns:
            bool: True if the value is a Houdini enum type, False otherwise.
        """
        return (isinstance(v, type)
                and any(isinstance(m, hou.EnumValue)
                        for n, m in get_members_safe(v)
                        if not n.startswith('_')
                        if not n == 'thisown')
                and all(isinstance(m, hou.EnumValue)
                        for n, m in get_members_safe(hou.primType)
                        if not n.startswith('_')
                        if n != 'thisown'))

    def mk_datum(item: Any, type: str, parent: HoudiniStaticData|None=None, name: str|None=None) -> HoudiniStaticData:
        """
        Create a HoudiniStaticData instance.

        Args:
            item (Any): The item to create a HoudiniStaticData instance for.
            type (str): The type of the item (e.g., 'module', 'class', 'function', 'constant', etc.).
            parent (HoudiniStaticData|None): The parent HoudiniStaticData instance, if any.
            name (str|None): The name of the item. If not provided, it will be derived from the item.
        Returns:
            HoudiniStaticData: An instance of HoudiniStaticData with the item's details.
        """
        name = name or getattr(item, '__name__', None) or str(item)
        assert name is not None, f"Item {item} has no name."
        datatype = dtype(item)
        if type == 'function' and parent and parent.type == 'class':
            type = 'method'
        if name == 'EnumValue':
            type = 'class'
        elif datatype == 'EnumValue':
            type = 'enum'
            datatype = parent.name if parent else datatype
        return HoudiniStaticData(
            name=name,
            type=type,
            datatype=datatype,
            docstring=docstring(item),
            houdini_version=houdini_version,
            parent_name=parent.name if parent else None,
            parent_type=parent.type if parent else None
        )
    module_dir = Path(hou.__file__).parent

    def load_module(module, parent: HoudiniStaticData|None=None) ->Generator[HoudiniStaticData, None, None]:
        """
        Load a module and its members, yielding HoudiniStaticData instances for each item.
        Args:
            module (module): The module to load.
            parent (HoudiniStaticData|None): The parent HoudiniStaticData instance, if any.
        Yields:
            HoudiniStaticData: An instance of HoudiniStaticData for each item found in the module.
        """
        if module in seen:
            return
        seen.add(module)
        file = getattr(module, '__file__', None)
        name = module.__name__
        if file is not None:
            file = Path(file).resolve()
            #if file.parent != module_dir:
            #    return
        else:
            file = module_dir / f"{module.__name__}.py"
        if name in IGNORE_MODULES:
            return
        module_data = mk_datum(module, 'module',
                               parent,
                               name=name)
        yield module_data
        for member_name, member in get_members_safe(module):
            if member_name.startswith('_'):
                continue
            if ismodule(member) or isinstance(member, moduleClass):
                yield from load_module(member,
                                       parent=module_data)
            elif isclass(member):
                yield from load_class(member,
                                      parent=module_data)
            elif isfunction(member):
                yield mk_datum(member, 'function',
                               parent=module_data,
                               name=member_name)
            elif isinstance(member, (Enum, hou.EnumValue)):
                yield mk_datum(member, 'EnumType',
                               parent=module_data,
                               name=member_name)
            elif isinstance(member, (Enum, hou.EnumValue)):
                yield mk_datum(member, 'enum',
                               parent=module_data,
                               name=member_name)
            elif (
                ismethod(member)
                or ismethoddescriptor(member)
                or isinstance(member, builtin_function_or_method)
            ):
                yield mk_datum(member, 'function',
                               parent=module_data,
                               name=member_name)
            else:
                yield mk_datum(member, 'object',
                               parent=module_data,
                               name=member_name)

    def load_class(cls, parent: HoudiniStaticData, name: str|None=None) ->Generator[HoudiniStaticData, None, None]:
        """
        Load class members and their static data.
        Args:
            cls (type): The class to load.
            parent (HoudiniStaticData): The parent HoudiniStaticData instance.
        Yields:
            HoudiniStaticData: An instance of HoudiniStaticData for each class member found.
        """
        if cls in seen:
            return
        seen.add(cls)
        name = name or cls.__name__
        if name.startswith('_'):
            return
        type = 'class'
        if cls is hou.EnumValue:
            type = 'class'
        if issubclass(cls, (Enum, hou.EnumValue)):
            type = 'enum'
        elif ishouenumtype(cls):
            type = 'EnumType'
        class_data = mk_datum(cls, type, parent)
        yield class_data
        for member_name, member in get_members_safe(cls):
            match member:
                case _ if ismethod(member):
                    type = 'bound-method'
                case _ if (isfunction(member)
                           or ismethoddescriptor(member)
                           or isinstance(member, builtin_function_or_method)
                ):
                    if parent.type == 'class':
                        type = 'method'
                    else:
                        type = 'function'
                case _ if isdatadescriptor(member):
                    type = 'attribute'
                case _ if isclass(member):
                    type = 'class'
                case _:
                    type = 'attribute'
            if name.startswith('_'):
                    continue

            if ismodule(member):
                yield from load_module(member,
                                       parent=class_data)
            elif isclass(member):
                yield from load_class(member,
                                      parent=class_data,
                                      name=f'{name}.{member_name}')
            elif isinstance(member, property):
                yield mk_datum(member, 'attribute',
                               parent=class_data,
                               name=member_name)
            else:
                yield mk_datum(member, type,
                               parent=class_data,
                               name=member_name)
    for module in MODULES:
        print(f'loading {module.__name__}...')
        yield from load_module(module)

def save_static_data_to_db(db_path='houdini_static_data.db'):
    """
    Save the static data to a SQLite database.

    Args:
        db_path (str): The path to the SQLite database file.
    """
    print('Opening database connection...')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print('Initializing tables...')
    cursor.execute('PRAGMA foreign_keys = ON;')
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS houdini_static_data (
            name TEXT NOT NULL,
            houdini_version TEXT NOT NULL,
            type TEXT NOT NULL,
            datatype TEXT NOT NULL,
            docstring TEXT,
            parent_version TEXT DEFAULT NULL REFERENCES houdini_static_data(houdini_version),
            parent_name TEXT DEFAULT NULL REFERENCES houdini_static_data(name),
            parent_type TEXT DEFAULT NULL REFERENCES houdini_static_data(type),
            PRIMARY KEY (houdini_version, name, type) ON CONFLICT REPLACE
            FOREIGN KEY (houdini_version, parent_name, parent_type) REFERENCES houdini_static_data(houdini_version, name, type)
        ) STRICT
    ''')

    print('Storing data...')
    previous: str = ''
    # Insert or update static data
    for datum in get_static_module_data():
        version = datum.houdini_version
        if datum.type == 'module':
            if previous != datum.name:
                print(f'Processing {datum.name}...')
        if datum.parent_name is not None:
            cursor.execute('''
                INSERT OR REPLACE INTO houdini_static_data (name, type, datatype, docstring, houdini_version, parent_version, parent_name, parent_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datum.name, datum.type, datum.datatype, datum.docstring, version, version, datum.parent_name, datum.parent_type))
        else:

            cursor.execute('PRAGMA foreign_keys = OFF')
            cursor.execute('''
                INSERT OR REPLACE INTO houdini_static_data (name, type, datatype, docstring, houdini_version)
                VALUES (?, ?, ?, ?, ?)
            ''', (datum.name, datum.type, datum.datatype, datum.docstring, version))
            cursor.execute('PRAGMA foreign_keys = ON;')

        conn.commit()

    cursor.execute('''
    VACUUM;
    ''')
    conn.close()

if __name__ == "__main__":
    # Get static data from Houdini
    static_data = get_static_module_data()
    # Save the static data to a database
    save_static_data_to_db()
    print("Static data saved to houdini_static_data.db")
#     """

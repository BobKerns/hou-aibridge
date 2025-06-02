'''
Routines to extract static data from Houdini 20.5.
'''

from pathlib import Path

import click

import hou

from zabob.common import (
    ZABOB_OUT_DIR, import_or_warn, save_static_data_to_db,
    InfiniteProxy,
)

if getattr(hou, 'ui', None) is None:
    hou.ui = InfiniteProxy(hou, 'hou.ui')
if getattr(hou, 'qt', None) is None:
    hou.qt = InfiniteProxy(hou, 'hou.qt')


MODULES = [
    loaded_module
    for m in (
        'builtins',
        'hou', 'pdg', 'hrpyc', 'soptoolutils', 'canvaseventtypes',
        'viewerstate', 'viewerstate.utils', '_alembic_hom_extensions',
        'pxr', 'husd', 'husd.objtranslator', 'husd.backgroundrenderer',
        'nodegraphview', 'nodegraphdisplay',
        'OpenGL', 'OpenGL.GL', 'OpenGL.GLU', 'OpenGL.GLUT', 'OpenGL.AGL',
        'MaterialX', 'coloraide', 'imageio', 'mercantile', 'PIL',
        'PyOpenColorIO', 'autorig', 'bakeanimation', 'baseinfowindow',
        'bvhviewer', 'channelwranglesnippet', 'charactertoolutils',
        'choptoolutils', 'clonecontrol',
        'cloud',
        'cloudEULA',
        'cloudsubmit',
        'cloudtoolutils',
        'colorschemeutils',
        'contextoptions',
        'cop2toolutils', 'coptoolutils', 'crowds',
        'crowdstoolutils', 'curveutils', 'defaultstatetools', 'defaulttoolmenus',
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
        'groom', 'groomingradial', 'haio', 'handleutils', 'hdefereval',
        'hjsonrpc',
        'hotkeys', 'hotkeys_prototype', 'houcppportion',
        'houdiniengineutils', 'houdinihelp', 'houdiniinternals',
        'houdiniInterpreter', 'houxmlrpc', 'hqrop', 'hscp',
        'husd', 'husdui', 'husktrace', 'hutil', 'hwebserver', 'images2gif',
        'inlinecpp', 'insertionpointutils', 'introspect',
        'karma_stats', 'keymaputils', 'landmarking', 'layout',
        'lightlinker',  'lightmixer', 'lightstate', 'logviewer',
        'lopcamutils', 'loplightandcamutils', 'lopshaderutils',
        'loptoolutils', 'loputils', 'lpetags', 'materiallinker',
        'metaexpr', 'modelview', 'mssbuild', 'mtlx2hda', 'mtlx2karma',
        'muscletoolutils', 'mvexportutils',
        'nodegraph',
        'nodegraphalign',
        'nodegraphautoscroll',
        'nodegraphbase',
        'nodegraphconnect',
        'nodegraphdisplay',
        'nodegraphdispopts',
        'nodegraphedittext',
        'nodegraphfastfind',
        'nodegraphflags',
        'nodegraphfurutils',
        'nodegraphgestures',
        'nodegraphhotkeys',
        'nodegraphlayout',
        'nodegraphpalettes',
        'nodegraphpopupmenus',
        'nodegraphprefs',
        'nodegraphquicknav',
        'nodegraphradialmenu',
        'nodegraphstates',
        'nodegraphrename',
        'nodegraphselectpos',
        'nodegraphselecthophooks',
        'nodegraphsnap',
        'nodegraphtitle',
        'nodegraphtopui',
        'nodegraphutils',
        'nodegraphvellumutils',
        'nodegraphview',
        'nodesearch', 'nodeselectionutil', 'nodethemes', 'nodeutils',
        'objecttoolutils', 'ocio',
        # 'opnode_sum', # Script, not module.

        'package',
        'packfoldermenu', 'parmutils', 'parsepeakuserlog',
        'particletoolutils', 'pdgd', 'pdgdatalayer', 'pdgjob',
        'pdgpathmap',
        'pdgservicepanel',
        'pdgstateserver',
        'pdgutils',
        # 'perfmon_sum', # Script, not module.
        'pluginutils', 'poselib', 'posespacedeform', 'pyro2',
        'pythonscriptmenu', 'quickplanes', 'radialmenu', 'recipetoolutils',
        'renderstats', 'rendertracker',
        'resourceui',
        'resourceutils',
        'rigtoolutils', 'rmands', 'roptoolutils', 'roputils',
        'sas', 'scenegraphdetails', 'scenegraphlayers',
        'sceneviewerhooks',
        # 'searchbox', # Needs QtApplication before QtPixmap
        'shaderhda',
        'shadingutils', 'shelfutils', 'shopclerks',
        'shoptoolutils', 'simtracker', 'skytoolutils',
        'snippetmenu', 'soptoolutils', 'soputils',
        'stagemanager', 'statehud', 'stateutils',
        'stroketoolutils',
        'taskgraphtable',
        'taskgraphtablepanel',
        'terraintoolutils', 'tilefx', 'toolprompts',
        'toolutils', 'top', 'topnettoolutils', 'toptoolutils',
        'toputils', 'uiutils', 'usdinlinelayermenu',
        'usdprimicons', 'usdrenderers', 'usdroputils',
        'vexpressionmenu', 'viewerhandle', 'viewerstate',
        'volumetoolutils', 'vop2mtlx', 'vopcallbacks',
        'vopfxmenu', 'vopnettoolutils', 'voptoolutils',
        'webapiclient',
    )
    for loaded_module in import_or_warn(m)
]

IGNORE_MODULES: frozenset[str] = frozenset[str]((
    # 'sys', 'os', 'itertools', 'time', 'xml', 'xmlrpc', 'json',
    # 're', 'subprocess', 'threading', 'multiprocessing', 'queue',
    # 'logging', 'warnings', 'contextlib', 'functools', 'collections',
    # 'collections.abc', 'itertools', 'operator', 'shutil', 'pathlib',
    # 'concurrent', 'concurrent.futures', 'asyncio',
    # 'socket', 'http', 'urllib',
    # 'json.decoder', 'json.encoder', 'json.scanner', 'typing',
    # 'sysconfig', 'importlib', 'importlib.util', 'builtins',
    # 'math', 'random', 'statistics', 'functools', 'select',
    # 'zlib', 'gzip', 'bz2', 'lzma', 'base64', 'hashlib',
    # 'pickle', 'copy', 'copyreg', 'marshal', 'struct',
    # 'array', 'weakref', 'types', 'codecs', 'encodings',
    # 'inspect', 'traceback', 'pprint', 'cProfile', 'profile',
    # 'timeit', 'cgitb', 'faulthandler', 'linecache', 'gc',
    # 'io', 'numbers', 'shlex', 'heapq', 'ast', 'abc', 'datetime',
    # 'csv', 'locale', 'fnmatch', 'glob', 'quopri', 'lxml.etree',
    # 'email', 'email.charset', 'email.errors', 'email.encoders',
    # 'contextvars', 'reprlib', 'signal', 'ssl', 'errno', 'html',
    # 'mimetypes', 'genericpath', 'posixpath', 'stat', 'platform',
    # 'binascii', 'resourceutils', 'future.standard_library',
    # 'concurrent.futures', 'ctypes', 'ctypes.util', 'ctypes.wintypes',
    # 'ctypes.macholib', 'ctypes.macholib.dyld', 'ctypes.macholib.framework',
    #'bisect', 'numpy', 'scipy', 'matplotlib', 'pandas',
    #'scikit-learn', 'sklearn', 'tensorflow', 'torch', 'torchvision',
    #'keras', 'tempfile', 'zipfile', 'tarfile', 'gzip', 'bz2',
    # 'zipimport', 'pkgutil', 'PySide2.support', 'atexit', 'fcntl',
    # 'lxml', 'markupsafe', 'string', 'mmap', 'posix',  'pwd', 'pyexpat',
    # 'readline', 'resource', 'shiboken2', 'keyword', 'simplejson',
    # 'decimal', 'termios', 'unicodedata', 'uuid', 'getpass', 'requests',
    # 'code', 'poster', 'bookish', 'flask', 'click', 'werkzeug',
    # 'dataclasses', 'textwrap', 'difflib', 'hnac', 'secrets', 'selectors',
    # 'jinja2', 'tokenize', 'pydoc', 'configparser', 'html.parser',
    # 'PySide2.QtWidgets', 'bookish.paths', 'bookish.search', 'urllib.parse',
    # 'ipaddress', 'calendar', 'bookish.wiki.langpaths', 'bookish.util',
    # 'jinja2.environment', 'jinja2.nodes', 'socketserver', 'codeop',
    # 'hutil.Qt.QtWidgets', 'enum', 'pytz', 'xmlrpc.client',
    # 'xml.parsers.expat', 'future', 'argparse', 'six',
    # 'bookish.functions', 'bookish.stores', 'QtCompat',
    # 'bookish.stores', 'bookish.compat',
    # 'bookish.text.textify', 'bookish.avenue.avenue',
    # 'bookish.wiki.pipeline', 'bookish.wiki.includes',
    # 'bookish.wiki.wikipages', 'bookish.wiki.styles',
    # 'bookish.avenue.patterns', 'bookish.langpath', 'jinja2.environment',
    # 'PySide2.QtGui',
))


default_db = ZABOB_OUT_DIR / hou.applicationVersionString() / 'houdini_static_data.db'
@click.command()
@click.argument('db', type=click.Path(exists=False, dir_okay=False, path_type=Path), default=default_db)
def main(db: Path=default_db):
    """
    Main function to save Houdini static data to a database.
    Args:
        db (Path): The path to the SQLite database file.
    """
    db.parent.mkdir(parents=True, exist_ok=True)
    save_static_data_to_db(db_path=db,
                           include=MODULES,
                           ignore=IGNORE_MODULES)
    print(f"Static data saved to {db}")

if __name__ == "__main__":
    main()

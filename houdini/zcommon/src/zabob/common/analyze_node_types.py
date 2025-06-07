'''
Analyze node types in Houdini installations.
'''

from pathlib import Path
import sqlite3
from collections.abc import Mapping
import sys
from typing import Any

import hou


from zabob.common.common_utils import get_name, none_or
from zabob.common.analysis_types import (
    NodeCategoryInfo,
    NodeTypeInfo,
    ParmTemplateInfo,
)
from zabob.common.analysis_db import analysis_db
from zabob.common.analyze_modules import analyze_modules, modules_in_path
from zabob.common.timer import timer


def _category_info(name: str, category: hou.NodeTypeCategory):
    """
    Extract information from a Houdini NodeTypeCategory.
    Returns a dictionary with category name and node types.

    Args:
        name (str): The name of the node type category.
        category (hou.NodeTypeCategory): The Houdini node type category to extract information from.
    Yields:
        NodeCategoryInfo: Information about the node category, including its name.
        NodeTypeInfo: Information about each node type within the category.
    """
    try:
        hasSubNetworkType = category.hasSubNetworkType()
    except hou.OperationFailed:
        # If the category does not support subnetwork types, we assume it does not have one.
        hasSubNetworkType = False
    yield NodeCategoryInfo(
        name=name,
        label=category.label(),
        hasSubnetworkType=hasSubNetworkType,
    )
    yield from (
        item
        for name, node_type in category.nodeTypes().items()
        for item in _node_type_info(name, node_type)
    )

def _node_type_info(name: str, node_type: hou.NodeType):
    """
    Extract information from a Houdini NodeType.
    Yields a NodeTypeInfo object with the node type name and category.
    Yields information about the node type's parameters.

    Args:
        name (str): The name of the node type.
        node_type (hou.NodeType): The Houdini node type to extract information from.
    Yields:
        NodeTypeInfo: Information about the node type, including its name, category, child category, description, and parameters.
        ParmTemplateInfo: Information about parameters of the node type.
    """
    deprecationInfo: dict[str, Any] = node_type.deprecationInfo() # type: ignore
    yield NodeTypeInfo(
        name=name,
        category=node_type.category().name(),
        childCategory=node_type.childTypeCategory().name() if node_type.childTypeCategory() else None,
        description=node_type.description(),
        helpUrl=node_type.helpUrl(),
        minNumInputs=node_type.minNumInputs(),
        maxNumInputs=node_type.maxNumInputs(),
        maxNumOutputs=node_type.maxNumOutputs(),
        isGenerator=node_type.isGenerator(),
        isManager=node_type.isManager(),
        isDeprecated=node_type.deprecated(), # type: ignore
        deprecation_reason=deprecationInfo.get('reason', None),
        deprecation_new_type=none_or(deprecationInfo.get('new_type', None), get_name),
        deprecation_version=deprecationInfo.get('version', None),
    )
    yield from (
        item
        for param in node_type.parmTemplates()
        for item in _parm_template_info(node_type, param)
    )

def _parm_template_info(node_type: hou.NodeType, parm: hou.ParmTemplate):
    """
    Extract information from a Houdini ParmTemplate.
    Yields a ParmTemplateInfo object with the parameter's type, name, label, and documentation.

    Args:
        node_type (hou.NodeType): The Houdini node type containing the parameter.
        param (hou.ParmTemplate): The parameter template to extract information from.
    Yields:
        ParmTemplateInfo: Information about the parameter template, including its type, name, label, and documentation.
    """
    def default_value(parm: hou.ParmTemplate) -> Any|None:
        """
        Get the default value of the parameter.
        Returns None if the parameter has no default value.
        """
        return parm.defaultValue() if hasattr(parm, 'defaultValue') else None # type: ignore
    yield ParmTemplateInfo(
        node_type_name=node_type.name(),
        node_type_category=node_type.category().name(),
        name=parm.name(),
        type=type(parm),
        template_type=parm.type(),
        defaultValue=default_value(parm),
        label=parm.label(),
        help=parm.help(),
        script=parm.scriptCallback(),
        script_language=get_name(parm.scriptCallbackLanguage()),
        tags=parm.tags()
    )


def analyze_categories():
    """
    Analyze node categories in the current Houdini session.
    Returns a dictionary mapping category names to their node types.

    Yields NodeCategoryInfo and NodeTypeInfo objects for each category and node type.

    This function iterates through all node type categories in Houdini,
    extracting information about each category and its node types.
    It yields NodeCategoryInfo for each category and NodeTypeInfo for each node type,
    including details such as the node type's name, category, child category, description,
    and parameters.

    Yields:
        NodeCategoryInfo: Information about each node category.
        NodeTypeInfo: Information about each node type within the categories.
        ParamTemplateInfo: Information about parameters of each node type.
    """
    print('Analyzing node categories...')
    yield from (item
            for name, category in hou.nodeTypeCategories().items()
            for item in _category_info(name, category))


def do_analysis(db_path: Path|None=None,
                connection: sqlite3.Connection|None=None,
                ignore: Mapping[str, str]|None =None,
                done: set[str]|None = None
                ):
    """
    Perform analysis of node types and modules in Houdini and store results in the database.

    Either a database path or an existing SQLite connection must be provided.
    If a database path is provided, a new connection will be created.
    If a connection is provided, it will be used directly, the creator is responsible for closing it.

    Args:
        db_path: Optional path to the database file.
        connection: Optional SQLite connection object.
        ignore: Optional mapping of module names to reasons for ignoring them.
        done: Optional set of module names that have already been processed.
    """
    done = done or set()
    ignore = ignore or {}
    with timer('Analyzing') as t:
        with analysis_db(db_path=db_path, connection=connection, write=True) as db:
            t('Analyzing node types...')
            yield from analyze_categories()
            t('Analyzing modules...')
            yield from analyze_modules(include=modules_in_path(sys.path,
                                                            done=done,
                                                            ignore=ignore),
                                    done=done,
                                    ignore=ignore,)

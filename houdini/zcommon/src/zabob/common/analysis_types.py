'''
Types in the analysis pipeline, especially those to be stored in the database.

This module needs to be loadable in non-Houdini environments,

Where possible, it uses the original objects, but Houdini-specific types
are converted to more generic types (generally `str`)
'''

from abc import abstractmethod
from pathlib import Path
from enum import StrEnum
from dataclasses import dataclass
import builtins
from typing import Any, Literal, Protocol, TypeVar, TypedDict, NotRequired, Union

from zabob.common.common_types import JsonData


T = TypeVar('T')

class EntryType(StrEnum):
    """
    Enum for entry types in the Houdini static data.
    """
    MODULE = 'MODULE'
    CLASS = 'CLASS'
    FUNCTION = 'FUNCTION'
    METHOD = 'METHOD'
    ENUM = 'ENUM'
    CONSTANT = 'CONSTANT'
    OBJECT = 'OBJECT'
    ATTRIBUTE = 'ATTRIBUTE'
    ENUM_TYPE = 'ENUMTYPE'
    OVERLOAD = 'OVERLOAD'  # Add overload type


@dataclass
class AnalysisDBItem:
    """
    Base class for items to be written to the analysis database.
    """
    pass

@dataclass
class HoudiniStaticData(AnalysisDBItem):
    """
    A class to represent static data extracted from Houdini 20.5.

    Attributes:
        name (str): The name of the Houdini item (module, class, function, etc.).
        type (str): The type of the Houdini item (e.g., 'module', 'class', 'function', 'constant', etc.).
        datatype (str): The data type of the Houdini item (e.g., `int`, `str`, `hou.EnumValue`, etc.).
        docstring (str|None): The docstring of the Houdini item, or `None` if not available.
        parent_name (str|None): The name of the parent Houdini item, if applicable.
        parent_type (str|None): The type of the parent Houdini item, if applicable.
    """
    name: str
    type: EntryType
    datatype: builtins.type
    docstring: str|None = None
    parent_name: str|None = None
    parent_type: str|None = None

@dataclass
class ModuleData(AnalysisDBItem):
    """
    A class to represent module data extracted from Houdini 20.5.

    Attributes:
        name (str): The name of the module.
        file (Path): The file path of the module.
    """
    name: str
    directory: Path|None = None
    file: Path|None=None
    count: int|None= None
    status: Literal['OK', 'IGNORE']|Exception|None = None
    reason: str|None = None
    def __post_init__(self):
        """
        Post-initialization to set the directory based on the file path.
        If the file is not None, set the directory to its parent path.
        """
        if self.file is not None:
            self.directory = self.file.parent
        if isinstance(self.status, Exception):
            if self.reason is None:
                self.reason = str(self.status)


class AnalysisDBWriter(Protocol):
    """
    Protocol for writing items to the analysis database.
    """
    @abstractmethod
    def __call__(self, item: 'T', /) -> 'T|AnalysisDBItem':
        """
        Write an item to the analysis database.

        Args:
            item (AnalysisDBItem): The item to write to the database.
        """
        ...


@dataclass
class NodeCategoryInfo(AnalysisDBItem):
    """
    Data class to hold information about a Houdini node category.
    """
    name: str
    label: str
    hasSubnetworkType: bool


@dataclass
class NodeTypeInfo(AnalysisDBItem):
    """
    Data class to hold information about a Houdini node type.
    """
    name: str
    category: str
    childCategory: str|None
    description: str
    helpUrl: str
    minNumInputs: int
    maxNumInputs: int
    maxNumOutputs: int
    isGenerator: bool
    isManager: bool
    isDeprecated: bool
    deprecation_reason: str|None
    deprecation_new_type: str|None
    deprecation_version: str|None


@dataclass
class ParmTemplateInfo(AnalysisDBItem):
    """
    Data class to hold information about a Houdini parameter template.
    """
    node_type_name: str
    node_type_category: str
    name: str
    type: builtins.type
    template_type: str
    defaultValue: JsonData
    label: str
    help: str
    script: str
    script_language: str
    tags: dict[str, str]


class ParameterSpec(TypedDict):
    """
    TypedDict for representing a function parameter specification.
    Used in function signature information embedded in JSON.

    Only the 'name', 'type', and 'kind' fields are required.
    Other fields are present only when applicable.
    """
    name: str  # Always present
    type: str  # Always present
    kind: str  # Always present - POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, VAR_POSITIONAL, KEYWORD_ONLY, VAR_KEYWORD
    is_optional: NotRequired[bool]  # Present only when parameter can be omitted
    default: NotRequired[JsonData]  # Present only when parameter has a default value


@dataclass
class AnalysisFunctionSignature(AnalysisDBItem):
    """Function signature information for a function or method."""
    func_name: str
    parameters: list[ParameterSpec]
    return_type: str
    parent_name: str
    parent_type: str
    is_overload: bool = False
    overload_index: int | None = None
    file_path: str | None = None
    line_number: int | None = None

    def __post_init__(self):
        # Ensure overload_index is 0 for non-overloaded functions
        if not self.is_overload:
            self.overload_index = 0

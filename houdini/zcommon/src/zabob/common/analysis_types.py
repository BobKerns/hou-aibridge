'''
Types in the analysis pipeline, especially those to be stored in the database.
'''

from abc import abstractmethod
from pathlib import Path
from enum import StrEnum
from dataclasses import dataclass
import builtins
from typing import Literal, Protocol, TypeVar
from collections.abc import Generator

T = TypeVar('T')

class EntryType(StrEnum):
    """
    Enum for entry types in the Houdini static data.
    """
    MODULE = 'module'
    CLASS = 'class'
    FUNCTION = 'function'
    METHOD = 'method'
    ENUM = 'enum'
    CONSTANT = 'constant'
    OBJECT = 'object'
    ATTRIBUTE = 'attribute'
    ENUM_TYPE = 'EnumType'


@dataclass
class HoudiniStaticData:
    """
    A class to represent static data extracted from Houdini 20.5.

    Attributes:
        name (str): The name of the Houdini item (module, class, function, etc.).
        type (str): The type of the Houdini item (e.g., 'module', 'class', 'function', 'constant', etc.).
        datatype (str): The data type of the Houdini item (e.g., 'int', 'str', 'hou.EnumValue', etc.).
        docstring (str|None): The docstring of the Houdini item, or None if not available.
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
class ModuleData:
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


@dataclass
class AnalysisDBItem:
    """
    Base class for items to be written to the analysis database.
    """
    pass


class AnalysisDBWriter(Protocol):
    """
    Protocol for writing items to the analysis database.
    """
    @abstractmethod
    def __call__(self, item: 'T', /) -> Generator['T|AnalysisDBItem', None, None]:
        """
        Write an item to the analysis database.

        Args:
            item (AnalysisDBItem): The item to write to the database.
        """
        ...

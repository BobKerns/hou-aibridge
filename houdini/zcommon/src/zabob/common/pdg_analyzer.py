"""
Analyze PDG (TOPs) node types, services, and work item structures.
Provides data extraction for the procedural dependency graph components.
"""

from collections.abc import Generator

import pdg
import hou

from zabob.common.analysis_types import PDGRegistryInfo
from zabob.common.common_utils import get_name

Top: hou.NodeTypeCategory = hou.nodeTypeCategories()['Top']

def analyze_pdg() -> Generator[PDGRegistryInfo, None, None]:
    """Extract information about all available PDG node types"""
    # Implementation will use hou.nodeTypeCategories() and filter for TOP nodes
    # ...
    for registry in (pdg.registeredType.Dependency, pdg.registeredType.Node,   # type: ignore
                     pdg.registeredType.Scheduler, pdg.registeredType.Service, # type: ignore
                     pdg.registeredType.WorkItem): # type: ignore
        # Iterate through registered types in the PDG registry
        for name in pdg.TypeRegistry.types().typeNames(registry): # type: ignore
            # For each type, create a PDGNodeTypeInfo object
            # This assumes hou.NodeType can be used to get the description and other info
            yield PDGRegistryInfo(
                name=name,
                registry=get_name(registry),
            )
    for tag in pdg.TypeRegistry.types().tags: # type: ignore
        # Iterate through tags in the PDG registry
        yield PDGRegistryInfo(
            name=tag,
            registry='Tag',
        )


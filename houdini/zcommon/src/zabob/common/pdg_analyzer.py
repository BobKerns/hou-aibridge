"""
Analyze PDG (TOPs) node types, services, and work item structures.
Provides data extraction for the procedural dependency graph components.
"""

import hou
from pathlib import Path
import inspect
from typing import Dict, List, Any, Generator, Optional
from dataclasses import dataclass

from zabob.common.analysis_types import AnalysisDBItem, EntryType
from zabob.common.common_utils import none_or, values

@dataclass
class PDGNodeTypeInfo(AnalysisDBItem):
    """Information about a PDG node type"""
    name: str
    category: str  # e.g., "scheduler", "processor", "fetcher"
    description: str
    parameters: Dict[str, Any]
    input_type: Optional[str] = None
    output_type: Optional[str] = None

@dataclass
class PDGServiceInfo(AnalysisDBItem):
    """Information about a PDG service"""
    name: str
    methods: List[Dict[str, Any]]
    description: str
    service_type: str

@dataclass
class PDGWorkItemInfo(AnalysisDBItem):
    """Standard structure of PDG work items"""
    attribute_types: Dict[str, str]
    state_transitions: List[Dict[str, str]]

def analyze_pdg_node_types() -> Generator[PDGNodeTypeInfo, None, None]:
    """Extract information about all available PDG node types"""
    # Implementation will use hou.nodeTypeCategories() and filter for TOP nodes
    # ...

def analyze_pdg_services() -> Generator[PDGServiceInfo, None, None]:
    """Extract information about PDG services"""
    # Implementation will examine pdg.serviceRegistry()
    # ...

def collect_pdg_data(db_path: Optional[Path] = None) -> int:
    """
    Collect PDG information and store it in the database

    Returns:
        Number of PDG items stored
    """
    # Similar to collect_and_store_overloads, but for PDG data
    # ...

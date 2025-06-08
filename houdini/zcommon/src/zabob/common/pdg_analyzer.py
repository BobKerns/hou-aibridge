"""
Analyze PDG (TOPs) node types, services, and work item structures.
Provides data extraction for the procedural dependency graph components.
"""

from pathlib import Path
from typing import Any
from dataclasses import dataclass
from collections.abc import Generator

from zabob.common.analysis_types import AnalysisDBItem
@dataclass
class PDGNodeTypeInfo(AnalysisDBItem):
    """Information about a PDG node type"""
    name: str
    category: str  # e.g., "scheduler", "processor", "fetcher"
    description: str
    parameters: dict[str, Any]
    input_type: str|None = None
    output_type: str|None = None

@dataclass
class PDGServiceInfo(AnalysisDBItem):
    """Information about a PDG service"""
    name: str
    methods: list[dict[str, Any]]
    description: str
    service_type: str

@dataclass
class PDGWorkItemInfo(AnalysisDBItem):
    """Standard structure of PDG work items"""
    attribute_types: dict[str, str]
    state_transitions: list[dict[str, str]]

def analyze_pdg_node_types() -> Generator[PDGNodeTypeInfo, None, None]:
    """Extract information about all available PDG node types"""
    # Implementation will use hou.nodeTypeCategories() and filter for TOP nodes
    # ...
    yield PDGNodeTypeInfo(
        name="ExampleNodeType",
        category="processor",
        description="An example PDG node type",
        parameters={
            "param1": "string",
            "param2": "int"
        },
        input_type="file",
        output_type="file"
    )


def analyze_pdg_services() -> Generator[PDGServiceInfo, None, None]:
    """Extract information about PDG services"""
    # Implementation will examine pdg.serviceRegistry()
    # ...
    yield PDGServiceInfo(
        name="ExampleService",
        methods=[
            {"name": "method1", "return_type": "void", "parameters": []},
            {"name": "method2", "return_type": "int", "parameters": ["string"]}
        ],
        description="An example PDG service",
        service_type="scheduler"
    )

def collect_pdg_data(db_path: Path|None = None) -> int:
    """
    Collect PDG information and store it in the database

    Returns:
        Number of PDG items stored
    """
    # Similar to collect_and_store_overloads, but for PDG data
    # ...
    return 0

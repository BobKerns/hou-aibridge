#!/usr/bin/env python3
"""
Example queries demonstrating how Zabob can help Houdini users understand complex workflows.
This simulates the kinds of questions users would ask when encountering large node graphs.
"""

import json
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from zabob.mcp.database import HoudiniDatabase

def format_response(data, title):
    """Format a response for display."""
    print(f"\n🎯 {title}")
    print("=" * (len(title) + 3))
    print(json.dumps(data, indent=2, default=str))

def simulate_user_questions():
    """Simulate real user questions about Houdini workflows."""

    print("🤖 Zabob: Houdini AI Assistant - Demo Session")
    print("Simulating how Zabob helps users understand complex Houdini workflows\n")

    db = HoudiniDatabase()

    with db:
        # Question 1: User encounters unfamiliar nodes in a graph
        print("👤 User: 'I'm looking at a node graph with lots of SOP nodes I don't recognize.'")
        print("🤖 Zabob: Let me show you what SOP nodes are available...")

        sop_nodes = db.get_node_types_by_category("Sop")
        sop_response = {
            "category": "Sop",
            "node_types": [
                {
                    "name": nt.name,
                    "description": nt.description,
                    "inputs": f"{nt.min_inputs}-{nt.max_inputs}",
                    "outputs": nt.max_outputs
                }
                for nt in sop_nodes[:10]  # Show first 10
            ],
            "total_available": len(sop_nodes)
        }
        format_response(sop_response, "SOP Node Types (Sample)")

        # Question 2: User needs to work with primitives programmatically
        print("\n👤 User: 'I need to select and modify groups of primitives in Python. What functions should I use?'")
        print("🤖 Zabob: Here are the primitive-related functions available...")

        prim_functions = db.get_primitive_related_functions()
        prim_response = {
            "functions": [
                {
                    "name": f.name,
                    "module": f.module,
                    "purpose": "primitive operations"
                }
                for f in prim_functions[:15]  # Show first 15
            ],
            "total_found": len(prim_functions),
            "recommendation": "Focus on hou.Geometry and hou.Prim modules for primitive operations"
        }
        format_response(prim_response, "Primitive Operation Functions")

        # Question 3: User wants to create nodes programmatically
        print("\n👤 User: 'How do I create nodes dynamically in my Python script?'")
        print("🤖 Zabob: Here are functions that return node objects...")

        node_functions = db.get_functions_returning_nodes()
        node_response = {
            "functions": [
                {
                    "name": f.name,
                    "module": f.module,
                    "returns": f.datatype
                }
                for f in node_functions[:10]  # Show first 10
            ],
            "total_found": len(node_functions),
            "tip": "Look for createNode() methods in parent container objects"
        }
        format_response(node_response, "Node Creation Functions")

        # Question 4: User searches for specific functionality
        print("\n👤 User: 'I need to work with transforms. What's available?'")
        print("🤖 Zabob: Searching for transform-related functions...")

        transform_functions = db.search_functions_by_keyword("transform", limit=12)
        transform_response = {
            "keyword": "transform",
            "functions": [
                {
                    "name": f.name,
                    "module": f.module,
                    "datatype": f.datatype
                }
                for f in transform_functions
            ],
            "count": len(transform_functions)
        }
        format_response(transform_response, "Transform-Related Functions")

        # Show database coverage
        print("\n👤 User: 'How comprehensive is your knowledge of Houdini?'")
        print("🤖 Zabob: Here's what I know about your Houdini installation...")

        stats = db.get_database_stats()
        coverage_response = {
            "database_path": str(db.db_path),
            "knowledge_base": stats,
            "capabilities": [
                "Complete function and class documentation",
                "All node types with parameters",
                "Module relationships and hierarchies",
                "Smart search across names and descriptions"
            ]
        }
        format_response(coverage_response, "Zabob's Knowledge Base")

    print("\n" + "="*60)
    print("✅ Demo Complete!")
    print("🎯 Value Proposition:")
    print("   • Instant answers about unfamiliar Houdini workflows")
    print("   • Programmatic assistance for Python scripting")
    print("   • Comprehensive database of all Houdini capabilities")
    print("   • AI-powered search and recommendations")
    print("   • Perfect for both beginners and experts working with complex graphs")

if __name__ == "__main__":
    try:
        simulate_user_questions()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

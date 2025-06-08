# Zabob MCP Server Demo Script
## For CGI Artists: Making Houdini's Python API Accessible

*Target Audience: Professional CGI artist learning PDG workflows*

---

## Introduction

The Zabob MCP server provides AI agents with comprehensive access to Houdini's Python API documentation, node types, and PDG registry. This demo shows how it can accelerate learning and development by providing instant, contextual information about Houdini's vast API.

**Setup**: The server connects to a SQLite database containing 20.5.584 Houdini API information with 131 PDG registry entries, thousands of functions, and complete node type documentation.

---

## Demo Scenario 1: "I need to understand geometry manipulation in Python"

**User Query**: *"What functions are available for working with primitives and geometry selection?"*

**Demo the tool**: `get_primitive_functions`

**Expected Response**: Functions like:
- `hou.Geometry.globPrims()` - Select primitives by pattern
- `hou.Geometry.primGroups()` - Get primitive groups
- `hou.PrimGroup.add()` - Add primitives to groups
- `hou.Prim.attribValue()` - Get primitive attributes

**Why this matters**: Shows how to bridge familiar SOP concepts into Python scripting.

---

## Demo Scenario 2: "I want to build node networks programmatically"

**User Query**: *"Show me all the functions that can create or return Houdini nodes"*

**Demo the tool**: `get_functions_returning_nodes`

**Expected Response**: Essential node creation functions:
- `hou.Node.createNode()` - Create child nodes
- `hou.ObjNode.createNode()` - Create object-level nodes
- `hou.SopNode.createOutputNode()` - Chain SOP nodes
- `hou.Node.parent()` - Navigate node hierarchy

**Why this matters**: Demonstrates how to automate complex network building tasks.

---

## Demo Scenario 3: "I need help with specific SOP nodes"

**User Query**: *"What SOP nodes are available for deformation and animation?"*

**Demo the tool**: `search_node_types` with keyword "deform"

**Expected Response**: Node types like:
- `lattice` - Lattice deformation
- `wiredeform` - Wire deformation
- `benddeform` - Bend deformation
- `twist` - Twist deformation

**Follow-up Query**: *"What about SOP nodes for particles?"*

**Demo the tool**: `get_node_types_by_category` with category "Sop", then search results

**Why this matters**: Helps discover relevant nodes without digging through menus.

---

## Demo Scenario 4: "I'm learning PDG but it's overwhelming"

**User Query**: *"What PDG node types are available for file operations?"*

**Demo the tool**: `search_pdg_registry` with keyword "file"

**Expected Response**: PDG entries like:
- `filecompress` (Node) - Compress files
- `filecopy` (Node) - Copy files
- `filedecompress` (Node) - Decompress files
- `File` (Dependency) - File dependency tracking

**Follow-up Query**: *"Show me all PDG scheduler types"*

**Demo the tool**: `get_pdg_registry` with registry_type "Scheduler"

**Expected Response**: Available schedulers like Local, HQueue, etc.

**Why this matters**: Makes PDG's component system more discoverable and less intimidating.

---

## Demo Scenario 5: "I want to script attribute operations"

**User Query**: *"Find functions related to attributes and point manipulation"*

**Demo the tool**: `search_functions` with keyword "attribute"

**Expected Response**: Functions like:
- `hou.Geometry.addAttrib()` - Create new attributes
- `hou.Point.setAttribValue()` - Set point attributes
- `hou.Geometry.findPointAttrib()` - Find existing attributes
- `hou.AttribType` - Attribute type constants

**Follow-up Query**: *"What about point cloud functions?"*

**Demo the tool**: `search_functions` with keyword "point"

**Why this matters**: Reveals the programmatic interface to familiar attribute workflows.

---

## Demo Scenario 6: "I need to understand the module structure"

**User Query**: *"Give me an overview of what's available in the Houdini Python modules"*

**Demo the tool**: `get_modules_summary`

**Expected Response**: Module breakdown showing:
- `hou` - Main module (800+ functions)
- `houapi` - Core API functions
- `hutil` - Utility functions
- `pdg` - PDG-specific functions
- Plus documentation status and function counts

**Why this matters**: Provides a roadmap of Houdini's Python ecosystem.

---

## Demo Scenario 7: "I'm working on a procedural pipeline"

**User Query**: *"What functions help with creating and managing TOP networks?"*

**Demo the tool**: `search_functions` with keyword "TOP"

**Expected Response**: Functions for:
- TOP network creation
- Work item management
- Scheduler configuration
- Dependency handling

**Follow-up Query**: *"Show me TOP-specific node types"*

**Demo the tool**: `get_node_types_by_category` with category "Top"

**Why this matters**: Helps build confidence with PDG workflows through familiar Python patterns.

---

## Demo Scenario 8: "I want to understand geometry cooking and caching"

**User Query**: *"Find functions related to geometry cooking and caching"*

**Demo the tool**: `search_functions` with keyword "cook"

**Expected Response**: Functions like:
- `hou.Node.cook()` - Force node evaluation
- `hou.SopNode.geometry()` - Get cooked geometry
- `hou.Geometry.freeze()` - Cache geometry state
- Various cooking control functions

**Why this matters**: Shows how to control Houdini's evaluation system programmatically.

---

## Demo Scenario 9: "I need database statistics for planning"

**User Query**: *"What's the scope of information available in this system?"*

**Demo the tool**: `get_database_stats`

**Expected Response**: Complete statistics:
- 131 PDG registry entries
- 2000+ functions documented
- 500+ node types cataloged
- Multiple categories covered
- Database version and location

**Why this matters**: Gives confidence in the comprehensiveness of the resource.

---

## Key Demo Talking Points

### 🎯 **For the CGI Professional**
- **Familiar concepts, new interface**: Translates SOP workflows into Python
- **Discovery over memorization**: Find functionality instead of memorizing syntax
- **PDG demystified**: Makes procedural dependency graphs more approachable
- **Production-ready**: Based on actual Houdini 20.5.584 documentation

### 🚀 **Time-Saving Benefits**
- **Instant API lookup**: No more browsing endless documentation
- **Contextual search**: Find exactly what you need when you need it
- **Pattern recognition**: See how similar operations work across different contexts
- **Confidence building**: Reduces intimidation factor of complex APIs

### 🔧 **Technical Advantages**
- **Always current**: Database reflects actual Houdini installation
- **Comprehensive coverage**: Functions, nodes, PDG registry, modules
- **Intelligent search**: Ranked results put best matches first
- **Structured output**: Clean, parseable responses for AI integration

---

## Demo Flow Suggestions

1. **Start familiar**: Begin with SOP nodes and geometry functions
2. **Build complexity**: Move to node creation and network building
3. **Introduce PDG**: Show how registry makes PDG more approachable
4. **Show scope**: Use database stats to demonstrate comprehensiveness
5. **Real-world scenarios**: End with practical workflow examples

This positions the tool as a bridge between familiar artistic concepts and Houdini's powerful but complex Python automation capabilities.

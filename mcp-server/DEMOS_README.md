# Zabob MCP Server Demos

This directory contains demo scripts showcasing the capabilities of the Zabob MCP server for CGI artists, particularly those learning PDG workflows in Houdini.

## Demo Files

### 📋 `DEMO_SCRIPT.md`

Comprehensive step-by-step demo script with:

- **Target Audience**: Professional CGI artist with 40+ years experience
- **9 Real-world scenarios** covering SOP nodes, PDG workflows, and Python automation
- **Talking points** for presentations
- **Progressive learning path** from familiar concepts to advanced automation

### 🔧 `quick_demo.py`

**Run this first!** Quick executable demo showing all MCP tools in action:

```bash
cd /Users/rwk/p/zabob/mcp-server
python quick_demo.py
```

- Tests database connection
- Demonstrates each tool with real results
- Shows current database statistics
- Perfect for initial validation

### 🎭 `interactive_demo.py`

Full interactive demonstration script with:

- Detailed scenario walkthroughs
- Realistic user queries and responses
- Professional formatting and presentation
- Comprehensive coverage of all capabilities

### 🧪 `test_pdg_registry.py`

Technical validation script for PDG registry functionality:

- Database connection testing
- PDG registry query validation
- Search functionality verification
- Error handling demonstration

## Key Demo Highlights

### For CGI Artists Learning PDG:

- **131 PDG registry entries** covering Nodes, Schedulers, Services
- **4,205+ node types** including all SOP and TOP nodes
- **Intelligent search** with ranked results
- **Familiar SOP workflow** bridge to Python automation

### Current Database Stats:

- 📊 **4,205 node types** (SOP, TOP, Object, etc.)
- 🔧 **131 PDG registry entries**
- 📅 **5 PDG schedulers** (Local, HQueue, etc.)
- 🎯 **147 TOP nodes** for procedural workflows

## Demo Scenarios Covered

1. **Geometry Manipulation** - Primitive and point operations
2. **Node Creation** - Programmatic network building
3. **SOP Discovery** - Finding deformation and animation nodes
4. **PDG File Operations** - Making PDG less intimidating
5. **Scheduler Options** - Understanding PDG execution
6. **Attribute Scripting** - Point/primitive attribute workflows
7. **TOP Workflows** - Procedural dependency graphs
8. **Module Overview** - Python API landscape
9. **System Scope** - Database comprehensiveness

## Value Proposition

**_"Makes Houdini's vast Python API instantly accessible to AI agents"_**

- 🚀 **Accelerates learning**: Reduces PDG intimidation factor
- 🎯 **Contextual discovery**: Find exactly what you need
- 🔗 **Bridges workflows**: SOP familiarity → Python automation
- 📚 **Comprehensive**: Based on actual Houdini 20.5.584 installation
- 🤖 **AI-ready**: Perfect for agent-assisted development

## Running the Demos

```bash
# Quick validation (recommended first step)
python quick_demo.py

# Full interactive demo
python interactive_demo.py

# PDG-specific testing
python test_pdg_registry.py

# Start the actual MCP server
python src/zabob/mcp/server.py --help-tools
python src/zabob/mcp/server.py  # Start server
```

## Target Audience Notes

**Professional CGI Artists**, especially those working with large, complex node graphs, integrating complex python scripts, or automating workflow with PDG.

These demos are designed to show how the Zabob MCP server can transform the learning experience by providing instant, contextual access to Houdini's complex API through natural language queries.

![Zabob and city banner](docs/images/zabob-banner.jpg)

# Houdini MCP Integration Development Overview

## Architecture

The project consists of three distinct layers:

### VSCode Chat Extension (TypeScript)

Provides the user interface within VSCode
Interacts with AI models through the VSCode Chat API
Communicates with the MCP server for Houdini-specific functionality

### MCP Server (Python 3.13+)

Central component that exposes Houdini information via the Model Context Protocol
Provides generic Houdini documentation, node information, and capabilities
Acts as a bridge between the VSCode extension and Houdini-specific services
Can use modern Python features without concern for Houdini compatibility

### Houdini Services (Python matching Houdini version)

Runs in the Houdini Python environment (Python 3.11 for Houdini 20.5)
Extracts information directly from Houdini
Enables interaction with Houdini instances (local or remote)
Must maintain compatibility with specific Houdini Python versions

### Testing Strategy

Testing is implemented across multiple environments:

#### Unit Tests

Test individual components in isolation
Use uv for dependency management
Run in Python 3.13 for MCP server tests
Run in Python 3.11 for Houdini service tests

#### Integration Tests

Test communication between components
Use Docker containers to simulate the full environment
Leverage SideFX's official Docker dependency list for container setup

#### Version Compatibility

Test against both oldest and newest builds for supported Houdini versions
Focus on Houdini 20.5 and newer
Dynamically identify available versions via SideFX's API

### Continuous Integration

The GitHub Actions workflow handles:

* **Build Matrix**

  * Dynamically builds test matrix based on available Houdini versions
  * Caches version information to minimize API calls to SideFX
  * Uses repository variables for configuration

* **Dependency Management**

  * Uses uv with caching for reproducible builds
  * Leverages standardized Docker containers for consistent environments

* **Containerization**

  * Utilizes Docker for isolated testing environments
  * Follows SideFX's official container approach for dependencies
  * Separates Python version requirements across components

### Development Workflow

#### Local Development

* Use Docker containers for consistent development environments
* Leverage caching for efficient testing
* Maintain separation between MCP server and Houdini environments

#### Contribution Model

* Contributions can focus on a single layer
* Documentation improvements are particularly welcome
* MIT license for all components

#### Design Principles

* Maintain clear separation between layers
* Handle version compatibility explicitly
* Focus on Houdini 20.5+ with Python 3.11+

## Key Technologies

* Model Context Protocol (MCP): Foundation for AI assistant integration
* Docker: Containerization for consistent environments
* GitHub Actions: CI/CD pipeline automation
* uv: Modern Python package management
* Houdini Python API: Core interaction with Houdini

## Future Directions

* Support for upcoming Houdini 21.0 release
* Extended node information extraction
* Live Houdini session integration
* Network visualization capabilities

### Integration Approaches with Houdini's HTTP Server

#### Option 1: Ignore Houdini's server

We'd bring our own complete MCP server. This would give full compatibility and also expose Houdini interfaces directly to other tools.

#### Option 2: MCP Server on Houdini's HTTP Server (Recommended)

Leveraging Houdini's built-in HTTP server as transport for the MCP protocol offers significant advantages:

* Native Integration: Uses Houdini's own mechanism for web communication
* Simplified Architecture: Reduces the number of separate services to maintain
* Authentication Reuse: May leverage Houdini's existing authentication mechanisms
* Stable Transport: Benefits from SideFX's maintenance of the HTTP server component
* Resource Efficiency: Avoids running redundant web servers

This approach would involve:

* Creating MCP endpoints within Houdini's HTTP server
* Implementing the MCP protocol handlers on these endpoints
* Maintaining the separation of concerns while sharing transport

Considerations for Implementation When implementing Option 2:

* Stability Assessment: Test Houdini's HTTP server under various loads to ensure reliability
* Version Compatibility: Verify consistent HTTP server behavior across Houdini versions
* Extension Points: Identify the proper extension mechanisms in Houdini's server
* Isolation: Ensure MCP functionality doesn't interfere with existing Houdini HTTP services
* Error Handling: Design robust error recovery that respects both MCP and Houdini protocols

Development Strategy

* Create a proof-of-concept implementation to validate feasibility
* Design clean abstraction layers that separate MCP protocol concerns from transport
* Implement comprehensive testing for the integrated solution
* Document the approach for contributors

#### Option 3: Ignore MCP, add rest endpoints on Houdini's server

Houdini would be a backend for

## Value Proposition Focus

As noted, the core value comes from:

* AI-Powered Introspection: Understanding Houdini networks and providing insights
* Interactive Updates: Allowing modifications via natural language
* Knowledge Integration: Combining Houdini documentation with contextual understanding

Visualization enhancements should remain secondary to these core benefits, serving primarily as demonstration tools rather than primary development goals.

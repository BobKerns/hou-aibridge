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

## Development Environment Setup

### Prerequisites

Development should work in any of Linux, MacOS, or Windows WSL. Development in a Windows environment without WSL will not be supported. (So far only tested on MacOS).

- [direnv](https://direnv.net/)
- [uv](https://docs.astral.sh/uv/)
- [nvm](https://github.com/nvm-sh/nvm)
- [pnpm](https://pnpm.io/) (for Node projects)
- Python (see `.python-version`)
- Node.js (see `.nvmrc`)

### Initial Setup

1. Install all prerequisites above.
2. Clone the repository.
3. In the project root, run:

```sh
direnv allow
```

   Repeat in any subproject directory if needed.
4. The environment will auto-configure based on `.envrc`, `.python-version`, and `.nvmrc`.

### Environment Details

- The `.envrc` file manages Python and Node environments per subproject.
- Subproject `.envrc` files are symlinks to the top-level one and respect local `.python-version`/`.nvmrc`.
- The `bin/` directory holds command-line tools. More information is available in [bin/README.md](bin/README.md).

### Running and Testing

- To run the MCP server: ...
- To run Houdini adaptors: ...
- To run the VSCode extension: ...
- To run tests: ...

### Troubleshooting

- If `direnv` doesn’t activate, check that it’s installed and enabled in your shell.
- If dependencies are missing, ensure you’ve run `direnv allow` and installed all prerequisites.
- For Node/Python version issues, check `.nvmrc` and `.python-version` in the relevant subproject.

The `devtool diagnostics environment` tool gives detected information about the environment, whether packaged or development.

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

- **Build Matrix**
  - Dynamically builds test matrix based on available Houdini versions
  - Caches version information to minimize API calls to SideFX
  - Uses repository variables for configuration

- **Dependency Management**

  - Uses uv with caching for reproducible builds
  - Leverages standardized Docker containers for consistent environments

- **Containerization**

  - Utilizes Docker for isolated testing environments
  - Follows SideFX's official container approach for dependencies
  - Separates Python version requirements across components

### Development Workflow

#### Local Development

- Use Docker containers for consistent development environments
- Leverage caching for efficient testing
- Maintain separation between MCP server and Houdini environments

#### Contribution Model

- Contributions can focus on a single layer
- Documentation improvements are particularly welcome
- MIT license for all components

#### Design Principles

- Maintain clear separation between layers
- Handle version compatibility explicitly
- Focus on Houdini 20.5+ with Python 3.11+

## Key Technologies

- Model Context Protocol (MCP): Foundation for AI assistant integration
- Docker: Containerization for consistent environments
- GitHub Actions: CI/CD pipeline automation
- uv: Modern Python package management
- Houdini Python API: Core interaction with Houdini

## Future Directions

- Support for upcoming Houdini 21.0 release
- Extended node information extraction
- Live Houdini session integration
- Network visualization capabilities

### Integration Approaches with Houdini's HTTP Server

#### Option 1: Ignore Houdini's server

We'd bring our own complete MCP server. This would give full compatibility and also expose Houdini interfaces directly to other tools.

#### Option 2: MCP Server on Houdini's HTTP Server (Recommended)

Leveraging Houdini's built-in HTTP server as transport for the MCP protocol offers significant advantages:

- Native Integration: Uses Houdini's own mechanism for web communication
- Simplified Architecture: Reduces the number of separate services to maintain
- Authentication Reuse: May leverage Houdini's existing authentication mechanisms
- Stable Transport: Benefits from SideFX's maintenance of the HTTP server component
- Resource Efficiency: Avoids running redundant web servers

This approach would involve:

- Creating MCP endpoints within Houdini's HTTP server
- Implementing the MCP protocol handlers on these endpoints
- Maintaining the separation of concerns while sharing transport

Considerations for Implementation When implementing Option 2:

- Stability Assessment: Test Houdini's HTTP server under various loads to ensure reliability
- Version Compatibility: Verify consistent HTTP server behavior across Houdini versions
- Extension Points: Identify the proper extension mechanisms in Houdini's server
- Isolation: Ensure MCP functionality doesn't interfere with existing Houdini HTTP services
- Error Handling: Design robust error recovery that respects both MCP and Houdini protocols

Development Strategy

- Create a proof-of-concept implementation to validate feasibility
- Design clean abstraction layers that separate MCP protocol concerns from transport
- Implement comprehensive testing for the integrated solution
- Document the approach for contributors

#### Option 3: Ignore MCP, add rest endpoints on Houdini's server

Houdini would be a backend for

## Value Proposition Focus

As noted, the core value comes from:

- AI-Powered Introspection: Understanding Houdini networks and providing insights
- Interactive Updates: Allowing modifications via natural language
- Knowledge Integration: Combining Houdini documentation with contextual understanding

Visualization enhancements should remain secondary to these core benefits, serving primarily as demonstration tools rather than primary development goals.

## Libraries to Preload for Houdini Integration

Here are categories of libraries Houdini users commonly need:

### Scientific Computing

- **NumPy/SciPy** - Essential for most technical workflows
- **SymPy** - Symbolic mathematics (useful for complex expressions)
- **pandas** - For tabular data manipulation

### VFX & Computer Graphics

- **OpenImageIO** - Image format handling
- **OpenColorIO** - Color management
- **OpenEXR** - HDR image manipulation
- **USD** libraries - Universal Scene Description
- **OpenVDB** Python bindings - Volume data manipulation
- **Alembic** - Animation caching
- **scikit-image** - Image processing workflows
- **pyembree** - For accelerated ray-tracing operations

### 3D Data Processing

- **trimesh** - Triangle mesh processing
- **Open3D** - Point cloud processing
- **PyMesh** - Mesh processing tools
- **meshio** - Mesh I/O for various formats

### Simulation & Physics

- **PyBullet** - Physics engine
- **FEniCS** - Finite element analysis
- **PySPH** - Smoothed Particle Hydrodynamics
- **pyPBD** - Position Based Dynamics

### Procedural Generation

- **noise** - Perlin/Simplex noise generation
- **Procedural Toolkit** - Procedural generation algorithms
- **Voxelfuse** - Voxel-based modeling

### Machine Learning

- **scikit-learn** - ML algorithms
- **TensorFlow/PyTorch** - Deep learning (for ML-assisted tools)
- **SciKit-Image** - Image processing

## File Formats & Interchange

- **plyfile** - PLY format handling
- **pyvista** - Visualization toolkit adapters
- **pyobj** - OBJ file handling
- **pydxf** - DXF file handling (CAD)

## Animation

- **pyanimation** - Animation curve utilities
- **BVH** tools - Motion capture data

## Domain-Specific

- **pyquaternion** - Quaternion math (for rotations)
- **colormath** - Color space conversions
- **colorsys** - Color system conversions
- **LuxCoreRender** - Physically-based rendering

## Other

- **matplotlib** - Plotting

### Geohashing Libraries

- **python-geohash** - Standard geohash implementation
- **h3** - Hexagonal hierarchical geospatial indexing system (Uber)
- **s2geometry** - Google's spherical geometry library with hierarchical indexing
- **quadkey** - Microsoft's quadtree-based tile addressing system

### Procedural City/World Generation

For synthetic training data generation:

- **OSM2World** - Converts OpenStreetMap data to 3D models
- **CityJSON** - Lightweight format for 3D city models
- **BlenderGIS** - Techniques adaptable to Houdini
- **SumoCity** - Traffic simulation integration
- **Mapbox API tools** - For realistic terrain and satellite imagery

### Synthetic Data Generation

Libraries specifically useful for AI training data:

- **synthetic-dataset-generation** - Tools for generating annotated synthetic data
- **scenenet** - Indoor scene generation
- **CARLA** - Open-source simulator for autonomous driving (integration possible)
- **AirSim** - Microsoft's simulator for drones and cars (data extraction)
- **World** Data Sources
- **SRTM** - Global elevation data
- **Mapzen** - Open source mapping platform
- **tangrams** - Scene definitions for realistic map visualization
- **citygen** - Procedural city generation
- **procedural-gl-js** - 3D mapping and terrain visualization

This comprehensive coverage addresses most Houdini workflows from modeling and simulation to rendering and data visualization.

# freecad-cli

A complete CLI harness for FreeCAD providing headless command-line access to CAD operations.

## Installation

```bash
uv sync

# Verify installation
uv run freecad-cli --version
uv run freecad-cli session health
```

## Prerequisites

- **FreeCAD** must be installed with `FreeCADCmd` accessible via:
  - System PATH
  - `FREECAD_CMD` environment variable
  - `--freecad-path` option
  - Standard install locations (auto-detected)

## Quick Start

```bash
# Check FreeCAD is available
freecad-cli session health

# Create a new document
freecad-cli document new myproject.FCStd

# Add a box
freecad-cli part box myproject.FCStd MyBox -l 10 -w 20 -h 30

# Add a cylinder
freecad-cli part cylinder myproject.FCStd MyCyl -r 5 -h 40

# Boolean union
freecad-cli boolean fuse myproject.FCStd Combined --base MyBox --tool MyCyl

# Measure the result
freecad-cli measure object myproject.FCStd Combined

# Export to STEP
freecad-cli export file myproject.FCStd output.step

# JSON output for agent consumption
freecad-cli --json object list myproject.FCStd
```

## Command Groups

| Group | Description |
|-------|-------------|
| `session` | Version, health, modules |
| `document` | Create, info, save documents |
| `object` | List, inspect, delete objects |
| `part` | Create primitives (box, cylinder, sphere, cone, torus) |
| `sketch` | Create sketches, add geometry and constraints |
| `partdesign` | Pad, pocket, revolve, fillet, chamfer |
| `boolean` | Fuse, cut, common, multi-fuse |
| `transform` | Move, rotate, mirror, copy |
| `export` | Export to STEP, STL, IGES, BREP, OBJ |
| `import` | Import from various CAD formats |
| `measure` | Volume, area, distance, bounding box |
| `repl` | Interactive REPL mode |

## JSON Mode

Add `--json` before any command for machine-readable output:

```bash
freecad-cli --json measure object doc.FCStd MyBox
```

Output:
```json
{
  "status": "ok",
  "object": "MyBox",
  "measurements": {
    "volume": 6000.0,
    "area": 2200.0,
    "dimensions": {"x": 10.0, "y": 20.0, "z": 30.0}
  }
}
```

## Interactive REPL

```bash
freecad-cli repl
freecad> open myproject.FCStd
freecad> objects
freecad> measure MyBox
freecad> quit
```

## Supported Export Formats

| Format | Extensions |
|--------|------------|
| STEP | .step, .stp |
| IGES | .iges, .igs |
| STL | .stl |
| BREP | .brep, .brp |
| OBJ | .obj |
| DAE | .dae |
| DXF | .dxf |
| SVG | .svg |

## Architecture

The CLI harness works by:
1. Generating Python scripts that use FreeCAD's API
2. Executing them via `FreeCADCmd` in headless mode
3. Extracting structured JSON results from stdout
4. Presenting output in human-readable or JSON format

No GUI is required. All state persists in `.FCStd` document files.

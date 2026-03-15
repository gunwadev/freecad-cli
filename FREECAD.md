# FreeCAD CLI Harness - Standard Operating Procedure

## Overview

The FreeCAD CLI harness (`freecad-cli`) provides a complete command-line interface for FreeCAD CAD operations. It wraps FreeCAD's Python API via headless `FreeCADCmd` execution, enabling scriptable and agent-consumable CAD workflows.

## Architecture

### Execution Model

Each CLI command:
1. Generates a self-contained Python script using FreeCAD's API
2. Executes it via `FreeCADCmd` (headless mode, no GUI)
3. Extracts JSON-encoded results from stdout using `__CLI_JSON__` markers
4. Presents results in human-readable or `--json` format

### State Model

- **File-based state**: All state persists in `.FCStd` documents on disk
- **No long-running process**: Each command is a standalone FreeCADCmd invocation
- **Idempotent reads**: Open/info/measure commands don't modify documents
- **Atomic writes**: Document modifications save atomically via FreeCAD's save mechanism

### FreeCADCmd Discovery

Priority order:
1. `--freecad-path` CLI option
2. `FREECAD_CMD` environment variable
3. System PATH (`which FreeCADCmd`)
4. Platform-specific search paths (macOS .app, Linux /usr/bin, conda, etc.)

## Command Groups

### session
- `version` - FreeCAD version info
- `health` - Connectivity/health check
- `modules` - List available workbenches

### document
- `new <path>` - Create new .FCStd document
- `info <path>` - Document details and object listing
- `save <path> [--as <newpath>]` - Save document

### object
- `list <path> [--type <filter>]` - List objects
- `info <path> <name>` - Inspect object properties
- `delete <path> <name>` - Remove object
- `edges <path> <name>` - List shape edges
- `faces <path> <name>` - List shape faces

### part (primitives)
- `box`, `cylinder`, `sphere`, `cone`, `torus` - Create primitive shapes
- All support `--x/--y/--z` positioning

### sketch
- `create <path> <name> [--plane XY|XZ|YZ]` - Create sketch
- `line`, `circle`, `arc`, `rect` - Add geometry
- `constrain` - Add constraints (Horizontal, Vertical, Distance, etc.)
- `info` - Sketch details

### partdesign
- `pad` - Extrude sketch into solid
- `pocket` - Subtractive extrusion
- `revolve` - Revolution
- `fillet` - Round edges
- `chamfer` - Chamfer edges

### boolean
- `fuse` - Union
- `cut` - Subtraction
- `common` - Intersection
- `multi-fuse` - Multi-shape union

### transform
- `move` - Translate (relative or absolute)
- `rotate` - Rotate around axis
- `mirror` - Mirror across plane
- `copy` - Duplicate object

### export
- `file <doc> <output> [--objects <names>]` - Export to STEP/STL/IGES/BREP/OBJ
- `formats` - List supported formats

### import
- `file <doc> <input>` - Import STEP/IGES/STL into document

### measure
- `object <doc> <name>` - Volume, area, topology, center of mass
- `distance <doc> <obj1> <obj2>` - Distance between objects
- `bounds <doc> [--object <name>]` - Bounding box

### repl
- Interactive mode with `open`, `new`, `info`, `objects`, `measure`, `run` commands

## Output Modes

### Human-readable (default)
```
volume: 6000.0
area: 2200.0
bounds:
  xmin: 0.0, xmax: 10.0
```

### JSON (`--json`)
```json
{
  "status": "ok",
  "object": {
    "name": "Box",
    "volume": 6000.0,
    "area": 2200.0
  }
}
```

## Error Handling

All errors return structured output:
```json
{
  "status": "error",
  "error": "Object not found: MyBox",
  "type": "ScriptExecutionError"
}
```

## Prerequisites

- **FreeCAD** installed with `FreeCADCmd` accessible
- **Python 3.10+**
- **click** package (installed automatically)

## Example Workflow

```bash
# Create document and add shapes
freecad-cli document new project.FCStd
freecad-cli part box project.FCStd MainBody -l 100 -w 50 -h 30
freecad-cli part cylinder project.FCStd Hole -r 5 -h 40 --x 50 --y 25

# Boolean subtraction
freecad-cli boolean cut project.FCStd BodyWithHole --base MainBody --tool Hole

# Measure result
freecad-cli measure object project.FCStd BodyWithHole

# Export to STEP
freecad-cli export file project.FCStd output.step --objects BodyWithHole

# JSON mode for agent consumption
freecad-cli --json measure object project.FCStd BodyWithHole
```

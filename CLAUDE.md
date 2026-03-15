# FreeCAD CLI - AI-Powered 3D Modeling from the Command Line

## What This Project Is

A command-line tool (`freecad-cli`) that lets you create 3D models, export them for 3D printing, and manipulate CAD files -- all without opening a GUI. It wraps FreeCAD's powerful CAD engine and makes it scriptable.

Built for use with Claude Code (or any AI assistant) to design and iterate on 3D-printable parts through conversation.

## Prerequisites

- **FreeCAD** must be installed: `brew install --cask freecad`
- **uv** for Python package management: `brew install uv`
- The CLI auto-detects FreeCAD's location. If it can't find it, set `FREECAD_CMD=/path/to/freecadcmd`

## Installation

```bash
uv sync
uv run freecad-cli --version
```

## How the CLI Works

Every command:
1. Generates a Python script using FreeCAD's API
2. Runs it headlessly via `FreeCADCmd` (no GUI window)
3. Returns structured results (human-readable or `--json`)

All state lives in `.FCStd` document files on disk. Each command is stateless.

## CLI Commands

| Group | Commands | Purpose |
|-------|----------|---------|
| `session` | `version`, `health`, `modules` | Check FreeCAD status |
| `document` | `new`, `info`, `save` | Create/manage .FCStd files |
| `object` | `list`, `info`, `delete`, `edges`, `faces` | Inspect/manage objects |
| `part` | `box`, `cylinder`, `sphere`, `cone`, `torus` | Create primitive shapes |
| `sketch` | `create`, `line`, `circle`, `arc`, `rect`, `constrain`, `info` | 2D sketch geometry |
| `partdesign` | `pad`, `pocket`, `revolve`, `fillet`, `chamfer` | Parametric 3D operations |
| `boolean` | `fuse`, `cut`, `common`, `multi-fuse` | Combine/subtract shapes |
| `transform` | `move`, `rotate`, `mirror`, `copy` | Position objects |
| `export` | `file`, `formats` | Export to STL, STEP, IGES, etc. |
| `import` | `file` | Import CAD files into a document |
| `measure` | `object`, `distance`, `bounds` | Measure geometry |
| `repl` | *(interactive)* | Interactive session mode |

### JSON Mode

Add `--json` before any command for machine-readable output:
```bash
freecad-cli --json measure object myfile.FCStd MyBox
```

## Output Folder Convention

Each design gets its own folder under `output/`:

```
output/
├── hydrojug-handle/        # One folder per design project
│   ├── build_script.py     # FreeCAD build script
│   ├── part_name.stl       # 3D-printable STL file(s)
│   └── source.FCStd        # Editable FreeCAD source
├── phone-stand/
│   └── ...
└── cable-clip/
    └── ...
```

**Rules:**
- New design request = new folder under `output/`
- Revised version = update files in same folder, delete old versions
- Always clean up `.FCBak`, `__pycache__`, and superseded files
- Keep only: final build script, final STLs, and FreeCAD source

## No Absolute Paths -- Ever

**This is a hard rule.** All files in this repo must be portable and work on any machine.

- **NEVER** use absolute paths like `/Users/someone/...` or `C:\Users\...` in any file
- **NEVER** include usernames, home directories, or machine-specific paths
- Build scripts must use **relative paths** from the script's own location:
  ```python
  import os
  script_dir = os.path.dirname(os.path.abspath(__file__))
  output_path = os.path.join(script_dir, 'my_part.stl')
  ```
- CLI commands should use **relative paths** from the working directory:
  ```bash
  freecad-cli document new ./output/my-design/part.FCStd
  ```

### File Portability

| File Type | Portable? | Notes |
|-----------|-----------|-------|
| `.stl` | Yes | Pure geometry. Works on any slicer, any OS, any printer. Send freely. |
| `.step` | Yes | Standard CAD interchange. Opens in any CAD software. |
| `.FCStd` | Yes | FreeCAD project file. Needs FreeCAD but works on any machine. |
| `.py` build scripts | Yes, if rules followed | Must use relative paths only. |

**To share a design with someone:** just send them the design folder (e.g., `hydrojug-handle/`). The STL files work immediately in any slicer. The build script can regenerate everything if they have FreeCAD.

## Building Complex Parts

The CLI commands handle primitives and simple operations. For complex/organic shapes, write a FreeCAD Python script directly:

```bash
# Execute a custom build script
freecadcmd output/my-design/build.py
```

Build scripts should:
- Use `Part.makeBox()`, `Part.makeCylinder()`, `.fuse()`, `.cut()` etc.
- Output JSON results with `__CLI_JSON__` markers (see `utils/json_output.py`)
- Save to `.FCStd` and export to `.stl` for printing
- **Use `os.path.dirname(os.path.abspath(__file__))` for all file paths**

See `output/hydrojug-handle/build_clamp_handle.py` for a real example.

## 3D Print Export Workflow

```bash
# 1. Create or open a document
freecad-cli document new output/my-design/part.FCStd

# 2. Build the geometry (CLI commands or custom script)
freecad-cli part box output/my-design/part.FCStd Body -l 50 -w 30 -h 10

# 3. Export STL for your slicer
freecad-cli export file output/my-design/part.FCStd output/my-design/part.stl

# 4. Also export STEP if you want to edit in other CAD software
freecad-cli export file output/my-design/part.FCStd output/my-design/part.step
```

## Running Tests

```bash
uv run pytest freecad_cli/tests/ -v
```

- Unit tests (54) run without FreeCAD
- E2E tests (28) require FreeCAD installed
- All 82 tests pass with FreeCAD 1.0.2

## Project Structure

```
freecad-cli/
├── CLAUDE.md                   # This file (AI assistant instructions)
├── FREECAD.md                  # Detailed SOP reference
├── pyproject.toml              # Project config (uv sync)
├── uv.lock                     # Locked dependencies
├── .gitignore
├── freecad_cli/                # The CLI package
│   ├── freecad_cli.py          # CLI entry point (Click)
│   ├── core/                   # Document, shapes, booleans, export, etc.
│   ├── utils/                  # Runner, JSON output, errors
│   └── tests/                  # Unit + E2E tests
└── output/                     # Design projects (one folder each)
    └── hydrojug-handle/        # Example: clamp-on handle for 3D printing
```

## Supported Export Formats

| Format | Extensions | Use Case |
|--------|------------|----------|
| STL | .stl | 3D printing (most slicers) |
| STEP | .step, .stp | CAD interchange (editable) |
| IGES | .iges, .igs | Legacy CAD interchange |
| BREP | .brep | OpenCASCADE native |
| OBJ | .obj | 3D rendering/visualization |
| DXF | .dxf | 2D drawings / laser cutting |

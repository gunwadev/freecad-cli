"""CLI entry point for FreeCAD harness - Click-based CLI with REPL support."""

import cmd
import json
import shlex
import sys
import traceback

import click

from freecad_cli.utils.json_output import print_result
from freecad_cli.utils.errors import FreeCADCLIError


# Global state
_json_mode = False
_freecad_path = None


def _get_opts():
    """Get current global options."""
    return {"json_mode": _json_mode, "freecad_path": _freecad_path}


def _output(data):
    """Print result using current output mode."""
    print_result(data, json_mode=_json_mode)


def _handle_error(e):
    """Handle an error and output it."""
    _output({"status": "error", "error": str(e), "type": type(e).__name__})
    if not _json_mode:
        sys.exit(1)


# ============================================================
# Main CLI Group
# ============================================================

@click.group()
@click.option("--json", "json_mode", is_flag=True, help="Output in JSON format.")
@click.option("--freecad-path", envvar="FREECAD_CMD",
              help="Path to FreeCADCmd executable.")
@click.version_option(version="0.1.0", prog_name="freecad-cli")
def cli(json_mode, freecad_path):
    """CLI harness for FreeCAD - headless CAD operations."""
    global _json_mode, _freecad_path
    _json_mode = json_mode
    _freecad_path = freecad_path


# ============================================================
# Session Commands
# ============================================================

@cli.group()
def session():
    """FreeCAD session management."""
    pass


@session.command()
def version():
    """Show FreeCAD version."""
    from freecad_cli.core.session import get_version
    try:
        result = get_version(freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@session.command()
def health():
    """Check FreeCAD health status."""
    from freecad_cli.core.session import check_health
    result = check_health(freecad_path=_freecad_path)
    _output(result)


@session.command("modules")
def list_modules():
    """List available FreeCAD modules."""
    from freecad_cli.core.session import list_modules as _list_modules
    try:
        result = _list_modules(freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Document Commands
# ============================================================

@cli.group()
def document():
    """Document management (create, open, save, info)."""
    pass


@document.command()
@click.argument("filepath")
@click.option("--label", help="Document label.")
def new(filepath, label):
    """Create a new FreeCAD document."""
    from freecad_cli.core.project import new_document
    try:
        result = new_document(filepath, label=label, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@document.command()
@click.argument("filepath")
def info(filepath):
    """Show detailed document information."""
    from freecad_cli.core.project import document_info
    try:
        result = document_info(filepath, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@document.command("save")
@click.argument("filepath")
@click.option("--as", "save_as", help="Save as a new file.")
def save_doc(filepath, save_as):
    """Save a document (optionally as a new file)."""
    from freecad_cli.core.project import save_document
    try:
        result = save_document(filepath, save_as=save_as, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Object Commands
# ============================================================

@cli.group()
def object():
    """Object operations (list, info, delete)."""
    pass


@object.command("list")
@click.argument("filepath")
@click.option("--type", "type_filter", help="Filter by type (e.g. Part::Feature).")
def list_objects(filepath, type_filter):
    """List objects in a document."""
    from freecad_cli.core.project import list_objects as _list_objects
    try:
        result = _list_objects(filepath, type_filter=type_filter,
                               freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@object.command()
@click.argument("filepath")
@click.argument("name")
def info(filepath, name):
    """Inspect a specific object."""
    from freecad_cli.core.inspect import inspect_object
    try:
        result = inspect_object(filepath, name, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@object.command()
@click.argument("filepath")
@click.argument("name")
def delete(filepath, name):
    """Delete an object from a document."""
    from freecad_cli.core.project import delete_object
    try:
        result = delete_object(filepath, name, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@object.command()
@click.argument("filepath")
@click.argument("name")
def edges(filepath, name):
    """List edges of an object."""
    from freecad_cli.core.inspect import list_edges
    try:
        result = list_edges(filepath, name, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@object.command()
@click.argument("filepath")
@click.argument("name")
def faces(filepath, name):
    """List faces of an object."""
    from freecad_cli.core.inspect import list_faces
    try:
        result = list_faces(filepath, name, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Part (Primitives) Commands
# ============================================================

@cli.group()
def part():
    """Create primitive shapes (box, cylinder, sphere, etc.)."""
    pass


@part.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--length", "-l", type=float, required=True, help="Box length (X).")
@click.option("--width", "-w", type=float, required=True, help="Box width (Y).")
@click.option("--height", "-h", type=float, required=True, help="Box height (Z).")
@click.option("--x", type=float, default=0, help="X position.")
@click.option("--y", type=float, default=0, help="Y position.")
@click.option("--z", type=float, default=0, help="Z position.")
def box(filepath, name, length, width, height, x, y, z):
    """Add a box primitive."""
    from freecad_cli.core.primitives import add_box
    try:
        result = add_box(filepath, name, length, width, height,
                         x=x, y=y, z=z, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@part.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--radius", "-r", type=float, required=True, help="Cylinder radius.")
@click.option("--height", "-h", type=float, required=True, help="Cylinder height.")
@click.option("--angle", type=float, default=360, help="Sweep angle.")
@click.option("--x", type=float, default=0, help="X position.")
@click.option("--y", type=float, default=0, help="Y position.")
@click.option("--z", type=float, default=0, help="Z position.")
def cylinder(filepath, name, radius, height, angle, x, y, z):
    """Add a cylinder primitive."""
    from freecad_cli.core.primitives import add_cylinder
    try:
        result = add_cylinder(filepath, name, radius, height,
                              angle=angle, x=x, y=y, z=z,
                              freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@part.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--radius", "-r", type=float, required=True, help="Sphere radius.")
@click.option("--x", type=float, default=0, help="X position.")
@click.option("--y", type=float, default=0, help="Y position.")
@click.option("--z", type=float, default=0, help="Z position.")
def sphere(filepath, name, radius, x, y, z):
    """Add a sphere primitive."""
    from freecad_cli.core.primitives import add_sphere
    try:
        result = add_sphere(filepath, name, radius,
                            x=x, y=y, z=z, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@part.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--radius1", type=float, required=True, help="Bottom radius.")
@click.option("--radius2", type=float, required=True, help="Top radius.")
@click.option("--height", "-h", type=float, required=True, help="Cone height.")
@click.option("--angle", type=float, default=360, help="Sweep angle.")
@click.option("--x", type=float, default=0, help="X position.")
@click.option("--y", type=float, default=0, help="Y position.")
@click.option("--z", type=float, default=0, help="Z position.")
def cone(filepath, name, radius1, radius2, height, angle, x, y, z):
    """Add a cone primitive."""
    from freecad_cli.core.primitives import add_cone
    try:
        result = add_cone(filepath, name, radius1, radius2, height,
                          angle=angle, x=x, y=y, z=z,
                          freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@part.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--radius1", type=float, required=True, help="Major radius.")
@click.option("--radius2", type=float, required=True, help="Minor radius.")
@click.option("--x", type=float, default=0, help="X position.")
@click.option("--y", type=float, default=0, help="Y position.")
@click.option("--z", type=float, default=0, help="Z position.")
def torus(filepath, name, radius1, radius2, x, y, z):
    """Add a torus primitive."""
    from freecad_cli.core.primitives import add_torus
    try:
        result = add_torus(filepath, name, radius1, radius2,
                           x=x, y=y, z=z, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Sketch Commands
# ============================================================

@cli.group()
def sketch():
    """Sketcher operations (create sketches, add geometry)."""
    pass


@sketch.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--plane", type=click.Choice(["XY", "XZ", "YZ"]), default="XY",
              help="Sketch plane.")
def create(filepath, name, plane):
    """Create a new sketch."""
    from freecad_cli.core.sketch import create_sketch
    try:
        result = create_sketch(filepath, name, plane=plane,
                               freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@sketch.command()
@click.argument("filepath")
@click.argument("sketch_name")
@click.option("--x1", type=float, required=True)
@click.option("--y1", type=float, required=True)
@click.option("--x2", type=float, required=True)
@click.option("--y2", type=float, required=True)
def line(filepath, sketch_name, x1, y1, x2, y2):
    """Add a line to a sketch."""
    from freecad_cli.core.sketch import add_line
    try:
        result = add_line(filepath, sketch_name, x1, y1, x2, y2,
                          freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@sketch.command()
@click.argument("filepath")
@click.argument("sketch_name")
@click.option("--cx", type=float, required=True, help="Center X.")
@click.option("--cy", type=float, required=True, help="Center Y.")
@click.option("--radius", "-r", type=float, required=True)
def circle(filepath, sketch_name, cx, cy, radius):
    """Add a circle to a sketch."""
    from freecad_cli.core.sketch import add_circle
    try:
        result = add_circle(filepath, sketch_name, cx, cy, radius,
                            freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@sketch.command()
@click.argument("filepath")
@click.argument("sketch_name")
@click.option("--cx", type=float, required=True, help="Center X.")
@click.option("--cy", type=float, required=True, help="Center Y.")
@click.option("--radius", "-r", type=float, required=True)
@click.option("--start-angle", type=float, required=True, help="Start angle (degrees).")
@click.option("--end-angle", type=float, required=True, help="End angle (degrees).")
def arc(filepath, sketch_name, cx, cy, radius, start_angle, end_angle):
    """Add an arc to a sketch."""
    from freecad_cli.core.sketch import add_arc
    try:
        result = add_arc(filepath, sketch_name, cx, cy, radius,
                         start_angle, end_angle, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@sketch.command()
@click.argument("filepath")
@click.argument("sketch_name")
@click.option("--x1", type=float, required=True, help="First corner X.")
@click.option("--y1", type=float, required=True, help="First corner Y.")
@click.option("--x2", type=float, required=True, help="Opposite corner X.")
@click.option("--y2", type=float, required=True, help="Opposite corner Y.")
def rect(filepath, sketch_name, x1, y1, x2, y2):
    """Add a rectangle to a sketch."""
    from freecad_cli.core.sketch import add_rectangle
    try:
        result = add_rectangle(filepath, sketch_name, x1, y1, x2, y2,
                               freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@sketch.command()
@click.argument("filepath")
@click.argument("sketch_name")
@click.option("--type", "constraint_type", required=True,
              help="Constraint type (Horizontal, Vertical, Distance, etc.).")
@click.option("--geo1", type=int, required=True, help="First geometry index.")
@click.option("--pt1", type=int, default=None, help="First point index.")
@click.option("--geo2", type=int, default=None, help="Second geometry index.")
@click.option("--pt2", type=int, default=None, help="Second point index.")
@click.option("--value", type=float, default=None, help="Constraint value.")
def constrain(filepath, sketch_name, constraint_type, geo1, pt1, geo2, pt2, value):
    """Add a constraint to a sketch."""
    from freecad_cli.core.sketch import add_constraint
    try:
        result = add_constraint(filepath, sketch_name, constraint_type,
                                geo1, point_idx1=pt1, geo_idx2=geo2,
                                point_idx2=pt2, value=value,
                                freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@sketch.command("info")
@click.argument("filepath")
@click.argument("sketch_name")
def sketch_info_cmd(filepath, sketch_name):
    """Show sketch details (geometry, constraints)."""
    from freecad_cli.core.sketch import sketch_info
    try:
        result = sketch_info(filepath, sketch_name, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# PartDesign Commands
# ============================================================

@cli.group()
def partdesign():
    """PartDesign operations (pad, pocket, revolve, fillet, chamfer)."""
    pass


@partdesign.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--sketch", "sketch_name", required=True, help="Sketch to pad.")
@click.option("--length", type=float, required=True, help="Pad length.")
@click.option("--symmetric", is_flag=True, help="Pad symmetrically.")
@click.option("--reversed", is_flag=True, help="Reverse direction.")
def pad(filepath, name, sketch_name, length, symmetric, reversed):
    """Pad (extrude) a sketch into a solid."""
    from freecad_cli.core.partdesign import pad as _pad
    try:
        result = _pad(filepath, name, sketch_name, length,
                      symmetric=symmetric, reversed=reversed,
                      freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@partdesign.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--sketch", "sketch_name", required=True, help="Sketch for pocket.")
@click.option("--depth", type=float, required=True, help="Pocket depth.")
@click.option("--through-all", is_flag=True, help="Pocket through entire solid.")
def pocket(filepath, name, sketch_name, depth, through_all):
    """Create a pocket (subtractive extrusion)."""
    from freecad_cli.core.partdesign import pocket as _pocket
    try:
        result = _pocket(filepath, name, sketch_name, depth,
                         through_all=through_all, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@partdesign.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--sketch", "sketch_name", required=True, help="Sketch to revolve.")
@click.option("--angle", type=float, default=360, help="Revolution angle (degrees).")
@click.option("--axis", type=click.Choice(["X", "Y", "Z"]), default="Y",
              help="Revolution axis.")
def revolve(filepath, name, sketch_name, angle, axis):
    """Revolve a sketch around an axis."""
    from freecad_cli.core.partdesign import revolve as _revolve
    try:
        result = _revolve(filepath, name, sketch_name, angle=angle, axis=axis,
                          freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@partdesign.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--base", required=True, help="Base object name.")
@click.option("--edges", required=True, help="Comma-separated edge indices (1-based).")
@click.option("--radius", type=float, required=True, help="Fillet radius.")
def fillet(filepath, name, base, edges, radius):
    """Apply fillet to edges."""
    from freecad_cli.core.partdesign import fillet as _fillet
    edge_indices = [int(e.strip()) for e in edges.split(",")]
    try:
        result = _fillet(filepath, name, base, edge_indices, radius,
                         freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@partdesign.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--base", required=True, help="Base object name.")
@click.option("--edges", required=True, help="Comma-separated edge indices (1-based).")
@click.option("--size", type=float, required=True, help="Chamfer size.")
def chamfer(filepath, name, base, edges, size):
    """Apply chamfer to edges."""
    from freecad_cli.core.partdesign import chamfer as _chamfer
    edge_indices = [int(e.strip()) for e in edges.split(",")]
    try:
        result = _chamfer(filepath, name, base, edge_indices, size,
                          freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Boolean Commands
# ============================================================

@cli.group()
def boolean():
    """Boolean operations (fuse, cut, common)."""
    pass


@boolean.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--base", required=True, help="Base object name.")
@click.option("--tool", required=True, help="Tool object name.")
def fuse(filepath, name, base, tool):
    """Union/fuse two shapes."""
    from freecad_cli.core.boolean import fuse as _fuse
    try:
        result = _fuse(filepath, name, base, tool, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@boolean.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--base", required=True, help="Base object name.")
@click.option("--tool", required=True, help="Tool object name.")
def cut(filepath, name, base, tool):
    """Subtract tool from base."""
    from freecad_cli.core.boolean import cut as _cut
    try:
        result = _cut(filepath, name, base, tool, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@boolean.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--base", required=True, help="Base object name.")
@click.option("--tool", required=True, help="Tool object name.")
def common(filepath, name, base, tool):
    """Intersection of two shapes."""
    from freecad_cli.core.boolean import common as _common
    try:
        result = _common(filepath, name, base, tool, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@boolean.command("multi-fuse")
@click.argument("filepath")
@click.argument("name")
@click.option("--shapes", required=True, help="Comma-separated shape names.")
def multi_fuse_cmd(filepath, name, shapes):
    """Fuse multiple shapes."""
    from freecad_cli.core.boolean import multi_fuse
    shape_names = [s.strip() for s in shapes.split(",")]
    try:
        result = multi_fuse(filepath, name, shape_names,
                            freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Transform Commands
# ============================================================

@cli.group()
def transform():
    """Transform objects (move, rotate, mirror, copy)."""
    pass


@transform.command()
@click.argument("filepath")
@click.argument("object_name")
@click.option("--dx", type=float, default=0, help="X translation.")
@click.option("--dy", type=float, default=0, help="Y translation.")
@click.option("--dz", type=float, default=0, help="Z translation.")
@click.option("--absolute", is_flag=True, help="Set absolute position.")
def move(filepath, object_name, dx, dy, dz, absolute):
    """Move an object."""
    from freecad_cli.core.transform import move as _move
    try:
        result = _move(filepath, object_name, dx=dx, dy=dy, dz=dz,
                       absolute=absolute, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@transform.command()
@click.argument("filepath")
@click.argument("object_name")
@click.option("--axis-x", type=float, default=0, help="Rotation axis X component.")
@click.option("--axis-y", type=float, default=0, help="Rotation axis Y component.")
@click.option("--axis-z", type=float, default=1, help="Rotation axis Z component.")
@click.option("--angle", type=float, required=True, help="Rotation angle (degrees).")
def rotate(filepath, object_name, axis_x, axis_y, axis_z, angle):
    """Rotate an object."""
    from freecad_cli.core.transform import rotate as _rotate
    try:
        result = _rotate(filepath, object_name, axis_x=axis_x, axis_y=axis_y,
                         axis_z=axis_z, angle=angle, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@transform.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--source", required=True, help="Source object name.")
@click.option("--plane", type=click.Choice(["XY", "XZ", "YZ"]), default="XY",
              help="Mirror plane.")
def mirror(filepath, name, source, plane):
    """Mirror an object."""
    from freecad_cli.core.transform import mirror as _mirror
    try:
        result = _mirror(filepath, name, source, plane=plane,
                         freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@transform.command()
@click.argument("filepath")
@click.argument("name")
@click.option("--source", required=True, help="Source object name.")
def copy(filepath, name, source):
    """Copy an object."""
    from freecad_cli.core.transform import copy as _copy
    try:
        result = _copy(filepath, name, source, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Export/Import Commands
# ============================================================

@cli.group("export")
def export_group():
    """Export to various formats (STEP, STL, IGES, etc.)."""
    pass


@export_group.command("file")
@click.argument("filepath")
@click.argument("output_path")
@click.option("--objects", help="Comma-separated object names (default: all).")
def export_file(filepath, output_path, objects):
    """Export objects to a file."""
    from freecad_cli.core.export import export_object
    obj_names = [o.strip() for o in objects.split(",")] if objects else None
    try:
        result = export_object(filepath, output_path, object_names=obj_names,
                               freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@export_group.command("formats")
def export_formats():
    """List supported export formats."""
    from freecad_cli.core.export import list_formats
    result = list_formats(freecad_path=_freecad_path)
    _output(result)


@cli.group("import")
def import_group():
    """Import from various formats."""
    pass


@import_group.command("file")
@click.argument("filepath")
@click.argument("input_path")
def import_file(filepath, input_path):
    """Import a file into a document."""
    from freecad_cli.core.export import import_file as _import_file
    try:
        result = _import_file(filepath, input_path, freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Measure Commands
# ============================================================

@cli.group()
def measure():
    """Measurement operations (volume, area, distance, bounds)."""
    pass


@measure.command("object")
@click.argument("filepath")
@click.argument("object_name")
def measure_object_cmd(filepath, object_name):
    """Measure an object's properties."""
    from freecad_cli.core.measure import measure_object
    try:
        result = measure_object(filepath, object_name,
                                freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@measure.command()
@click.argument("filepath")
@click.argument("object1")
@click.argument("object2")
def distance(filepath, object1, object2):
    """Measure distance between two objects."""
    from freecad_cli.core.measure import distance_between
    try:
        result = distance_between(filepath, object1, object2,
                                  freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


@measure.command()
@click.argument("filepath")
@click.option("--object", "object_name", help="Specific object (default: all).")
def bounds(filepath, object_name):
    """Get bounding box."""
    from freecad_cli.core.measure import bounding_box
    try:
        result = bounding_box(filepath, object_name=object_name,
                              freecad_path=_freecad_path)
        _output(result)
    except FreeCADCLIError as e:
        _handle_error(e)


# ============================================================
# Printer Commands
# ============================================================

@cli.group()
def printer():
    """Manage 3D printer profiles."""
    pass


@printer.command()
@click.argument("name")
@click.option("--model", help="Full printer model name.")
@click.option("--bed-x", type=float, help="Build volume X (mm).")
@click.option("--bed-y", type=float, help="Build volume Y (mm).")
@click.option("--bed-z", type=float, help="Build volume Z (mm).")
@click.option("--nozzle", type=float, default=0.4, help="Nozzle diameter (mm).")
@click.option("--materials", help="Comma-separated materials (e.g., PLA,PETG,TPU).")
@click.option("--heated-bed/--no-heated-bed", default=True, help="Has heated bed.")
@click.option("--notes", help="Extra notes about the printer.")
def add(name, model, bed_x, bed_y, bed_z, nozzle, materials, heated_bed, notes):
    """Add a printer profile."""
    from freecad_cli.core.printer import add_printer
    mat_list = [m.strip() for m in materials.split(",")] if materials else None
    result = add_printer(name, model=model, bed_x=bed_x, bed_y=bed_y, bed_z=bed_z,
                         nozzle=nozzle, materials=mat_list, heated_bed=heated_bed,
                         notes=notes)
    _output(result)


@printer.command("list")
def list_printers_cmd():
    """List all printer profiles."""
    from freecad_cli.core.printer import list_printers
    _output(list_printers())


@printer.command()
@click.argument("name", required=False)
def info(name):
    """Show printer profile (default printer if no name given)."""
    from freecad_cli.core.printer import get_printer
    _output(get_printer(name))


@printer.command()
@click.argument("name")
def remove(name):
    """Remove a printer profile."""
    from freecad_cli.core.printer import remove_printer
    _output(remove_printer(name))


@printer.command("set-default")
@click.argument("name")
def set_default_cmd(name):
    """Set the default printer."""
    from freecad_cli.core.printer import set_default
    _output(set_default(name))


@printer.command()
@click.argument("name", required=False)
def settings(name):
    """Show recommended print settings for a printer."""
    from freecad_cli.core.printer import get_print_settings
    _output(get_print_settings(name))


# ============================================================
# REPL Mode
# ============================================================

class FreeCADREPL(cmd.Cmd):
    """Interactive REPL for FreeCAD CLI."""

    intro = "FreeCAD CLI REPL. Type 'help' for commands, 'quit' to exit."
    prompt = "freecad> "

    def __init__(self):
        super().__init__()
        self.current_file = None

    def do_open(self, arg):
        """Open a document: open <filepath>"""
        if not arg:
            print("Usage: open <filepath>")
            return
        self.current_file = arg.strip()
        try:
            from freecad_cli.core.project import open_document
            result = open_document(self.current_file, freecad_path=_freecad_path)
            _output(result)
        except Exception as e:
            print(f"Error: {e}")

    def do_new(self, arg):
        """Create a new document: new <filepath>"""
        if not arg:
            print("Usage: new <filepath>")
            return
        self.current_file = arg.strip()
        try:
            from freecad_cli.core.project import new_document
            result = new_document(self.current_file, freecad_path=_freecad_path)
            _output(result)
        except Exception as e:
            print(f"Error: {e}")

    def do_info(self, arg):
        """Show document info: info [filepath]"""
        fp = arg.strip() or self.current_file
        if not fp:
            print("No document open. Use 'open <filepath>' first.")
            return
        try:
            from freecad_cli.core.project import document_info
            result = document_info(fp, freecad_path=_freecad_path)
            _output(result)
        except Exception as e:
            print(f"Error: {e}")

    def do_objects(self, arg):
        """List objects: objects [filepath]"""
        fp = arg.strip() or self.current_file
        if not fp:
            print("No document open.")
            return
        try:
            from freecad_cli.core.project import list_objects
            result = list_objects(fp, freecad_path=_freecad_path)
            _output(result)
        except Exception as e:
            print(f"Error: {e}")

    def do_measure(self, arg):
        """Measure an object: measure <object_name> [filepath]"""
        parts = arg.strip().split()
        if not parts:
            print("Usage: measure <object_name> [filepath]")
            return
        obj_name = parts[0]
        fp = parts[1] if len(parts) > 1 else self.current_file
        if not fp:
            print("No document open.")
            return
        try:
            from freecad_cli.core.measure import measure_object
            result = measure_object(fp, obj_name, freecad_path=_freecad_path)
            _output(result)
        except Exception as e:
            print(f"Error: {e}")

    def do_version(self, arg):
        """Show FreeCAD version."""
        try:
            from freecad_cli.core.session import get_version
            result = get_version(freecad_path=_freecad_path)
            _output(result)
        except Exception as e:
            print(f"Error: {e}")

    def do_run(self, arg):
        """Run a CLI command: run <command args...>"""
        if not arg:
            print("Usage: run <command args...>")
            return
        try:
            argv = shlex.split(arg)
            cli(argv, standalone_mode=False)
        except SystemExit:
            pass
        except Exception as e:
            print(f"Error: {e}")

    def do_quit(self, arg):
        """Exit the REPL."""
        return True

    def do_exit(self, arg):
        """Exit the REPL."""
        return True

    do_EOF = do_quit


@cli.command()
def repl():
    """Start interactive REPL mode."""
    FreeCADREPL().cmdloop()


# ============================================================
# Entry Point
# ============================================================

def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

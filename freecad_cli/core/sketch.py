"""Sketcher operations for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def create_sketch(filepath, name, plane="XY", freecad_path=None):
    """Create a new sketch on a specified plane.

    Args:
        filepath: Path to .FCStd file.
        name: Sketch object name.
        plane: Sketch plane ("XY", "XZ", "YZ").

    Returns:
        Dict with sketch info.
    """
    filepath = os.path.abspath(filepath)

    plane_map = {
        "XY": "FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(0,0,0,1))",
        "XZ": "FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(1,0,0), -90))",
        "YZ": "FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))",
    }
    placement = plane_map.get(plane.upper(), plane_map["XY"])

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Sketcher
import Part

sketch = doc.addObject("Sketcher::SketchObject", {repr(name)})
sketch.Placement = {placement}
doc.recompute()
doc.save()

_output({{
    "status": "ok",
    "sketch": {{
        "name": sketch.Name,
        "label": sketch.Label,
        "plane": {repr(plane.upper())},
        "geometry_count": len(sketch.Geometry),
        "constraint_count": len(sketch.Constraints) if hasattr(sketch, 'Constraints') and sketch.Constraints else 0,
    }},
    "filepath": {repr(filepath)},
}})
"""
    return run_script(code, freecad_path=freecad_path)


def add_line(filepath, sketch_name, x1, y1, x2, y2, freecad_path=None):
    """Add a line segment to a sketch.

    Args:
        filepath: Path to .FCStd file.
        sketch_name: Name of the sketch object.
        x1, y1: Start point.
        x2, y2: End point.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Sketcher
import Part

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    idx = sketch.addGeometry(
        Part.LineSegment(FreeCAD.Vector({x1}, {y1}, 0), FreeCAD.Vector({x2}, {y2}, 0)),
        False
    )
    doc.recompute()
    doc.save()
    _output({{
        "status": "ok",
        "geometry_index": idx,
        "type": "line",
        "start": {{"x": {x1}, "y": {y1}}},
        "end": {{"x": {x2}, "y": {y2}}},
        "sketch": sketch.Name,
        "filepath": {repr(filepath)},
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def add_circle(filepath, sketch_name, cx, cy, radius, freecad_path=None):
    """Add a circle to a sketch.

    Args:
        filepath: Path to .FCStd file.
        sketch_name: Name of the sketch object.
        cx, cy: Center point.
        radius: Circle radius.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Sketcher
import Part

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    idx = sketch.addGeometry(
        Part.Circle(FreeCAD.Vector({cx}, {cy}, 0), FreeCAD.Vector(0, 0, 1), {radius}),
        False
    )
    doc.recompute()
    doc.save()
    _output({{
        "status": "ok",
        "geometry_index": idx,
        "type": "circle",
        "center": {{"x": {cx}, "y": {cy}}},
        "radius": {radius},
        "sketch": sketch.Name,
        "filepath": {repr(filepath)},
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def add_arc(filepath, sketch_name, cx, cy, radius, start_angle, end_angle,
            freecad_path=None):
    """Add an arc to a sketch.

    Args:
        filepath: Path to .FCStd file.
        sketch_name: Name of the sketch object.
        cx, cy: Center point.
        radius: Arc radius.
        start_angle, end_angle: Arc angles in degrees.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Sketcher
import Part
import math

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    sa = math.radians({start_angle})
    ea = math.radians({end_angle})
    idx = sketch.addGeometry(
        Part.ArcOfCircle(
            Part.Circle(FreeCAD.Vector({cx}, {cy}, 0), FreeCAD.Vector(0, 0, 1), {radius}),
            sa, ea
        ),
        False
    )
    doc.recompute()
    doc.save()
    _output({{
        "status": "ok",
        "geometry_index": idx,
        "type": "arc",
        "center": {{"x": {cx}, "y": {cy}}},
        "radius": {radius},
        "start_angle": {start_angle},
        "end_angle": {end_angle},
        "sketch": sketch.Name,
        "filepath": {repr(filepath)},
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def add_rectangle(filepath, sketch_name, x1, y1, x2, y2, freecad_path=None):
    """Add a rectangle to a sketch (4 constrained lines).

    Args:
        filepath: Path to .FCStd file.
        sketch_name: Name of the sketch object.
        x1, y1: First corner.
        x2, y2: Opposite corner.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Sketcher
import Part

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    x1, y1, x2, y2 = {x1}, {y1}, {x2}, {y2}
    # Add 4 lines
    l0 = sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(x1, y1, 0), FreeCAD.Vector(x2, y1, 0)), False)
    l1 = sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(x2, y1, 0), FreeCAD.Vector(x2, y2, 0)), False)
    l2 = sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(x2, y2, 0), FreeCAD.Vector(x1, y2, 0)), False)
    l3 = sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(x1, y2, 0), FreeCAD.Vector(x1, y1, 0)), False)

    # Connect corners
    sketch.addConstraint(Sketcher.Constraint("Coincident", l0, 2, l1, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", l1, 2, l2, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", l2, 2, l3, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", l3, 2, l0, 1))

    # Horizontal/vertical constraints
    sketch.addConstraint(Sketcher.Constraint("Horizontal", l0))
    sketch.addConstraint(Sketcher.Constraint("Horizontal", l2))
    sketch.addConstraint(Sketcher.Constraint("Vertical", l1))
    sketch.addConstraint(Sketcher.Constraint("Vertical", l3))

    doc.recompute()
    doc.save()
    _output({{
        "status": "ok",
        "geometry_indices": [l0, l1, l2, l3],
        "type": "rectangle",
        "corner1": {{"x": x1, "y": y1}},
        "corner2": {{"x": x2, "y": y2}},
        "sketch": sketch.Name,
        "filepath": {repr(filepath)},
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def add_constraint(filepath, sketch_name, constraint_type, geo_idx1,
                   point_idx1=None, geo_idx2=None, point_idx2=None,
                   value=None, freecad_path=None):
    """Add a constraint to a sketch.

    Args:
        filepath: Path to .FCStd file.
        sketch_name: Name of the sketch object.
        constraint_type: Type (e.g., "Horizontal", "Vertical", "Distance",
                         "Coincident", "Perpendicular", "Parallel", "Equal",
                         "Tangent", "Angle", "DistanceX", "DistanceY", "Radius").
        geo_idx1: First geometry index.
        point_idx1: Optional first point index.
        geo_idx2: Optional second geometry index.
        point_idx2: Optional second point index.
        value: Optional constraint value (for dimensional constraints).
    """
    filepath = os.path.abspath(filepath)

    # Build constraint args
    args = [repr(constraint_type), str(geo_idx1)]
    if point_idx1 is not None:
        args.append(str(point_idx1))
    if geo_idx2 is not None:
        args.append(str(geo_idx2))
    if point_idx2 is not None:
        args.append(str(point_idx2))
    if value is not None:
        args.append(str(value))
    constraint_args = ", ".join(args)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Sketcher

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    idx = sketch.addConstraint(Sketcher.Constraint({constraint_args}))
    doc.recompute()
    doc.save()
    _output({{
        "status": "ok",
        "constraint_index": idx,
        "type": {repr(constraint_type)},
        "sketch": sketch.Name,
        "filepath": {repr(filepath)},
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def sketch_info(filepath, sketch_name, freecad_path=None):
    """Get detailed info about a sketch.

    Args:
        filepath: Path to .FCStd file.
        sketch_name: Name of the sketch object.

    Returns:
        Dict with sketch details.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Sketcher

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    geometry = []
    for i, geo in enumerate(sketch.Geometry):
        g = {{"index": i, "type": type(geo).__name__}}
        if hasattr(geo, 'StartPoint') and hasattr(geo, 'EndPoint'):
            g["start"] = {{"x": geo.StartPoint.x, "y": geo.StartPoint.y}}
            g["end"] = {{"x": geo.EndPoint.x, "y": geo.EndPoint.y}}
        if hasattr(geo, 'Center'):
            g["center"] = {{"x": geo.Center.x, "y": geo.Center.y}}
        if hasattr(geo, 'Radius'):
            g["radius"] = geo.Radius
        geometry.append(g)

    constraints = []
    if hasattr(sketch, 'Constraints') and sketch.Constraints:
        for i, c in enumerate(sketch.Constraints):
            constraints.append({{
                "index": i,
                "type": c.Type,
                "first": c.First,
                "second": c.Second if c.Second != -2000 else None,
                "value": c.Value if c.Value != 0 else None,
            }})

    fc = getattr(sketch, 'FullyConstrained', False)

    _output({{
        "status": "ok",
        "sketch": {{
            "name": sketch.Name,
            "label": sketch.Label,
            "plane": "custom",
            "fully_constrained": fc,
            "geometry_count": len(geometry),
            "constraint_count": len(constraints),
            "geometry": geometry,
            "constraints": constraints,
        }},
        "filepath": {repr(filepath)},
    }})
"""
    return run_script(code, freecad_path=freecad_path)

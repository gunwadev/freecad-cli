"""Measurement operations for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def measure_object(filepath, object_name, freecad_path=None):
    """Measure an object's geometric properties.

    Args:
        filepath: Path to .FCStd file.
        object_name: Name of the object.

    Returns:
        Dict with measurements (volume, area, bounds, center of mass).
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
elif not hasattr(obj, 'Shape'):
    _output({{"status": "error", "error": "Object has no shape: " + {repr(object_name)}}})
else:
    shape = obj.Shape
    bb = shape.BoundBox
    com = shape.CenterOfMass if hasattr(shape, 'CenterOfMass') else None

    measurements = {{
        "volume": shape.Volume,
        "area": shape.Area,
        "length": shape.Length if hasattr(shape, 'Length') else 0,
        "bounds": {{
            "xmin": bb.XMin, "xmax": bb.XMax,
            "ymin": bb.YMin, "ymax": bb.YMax,
            "zmin": bb.ZMin, "zmax": bb.ZMax,
            "diagonal": bb.DiagonalLength,
        }},
        "dimensions": {{
            "x": bb.XLength,
            "y": bb.YLength,
            "z": bb.ZLength,
        }},
    }}
    if com:
        measurements["center_of_mass"] = {{"x": com.x, "y": com.y, "z": com.z}}

    # Count topology
    measurements["topology"] = {{
        "vertices": len(shape.Vertexes),
        "edges": len(shape.Edges),
        "faces": len(shape.Faces),
        "solids": len(shape.Solids),
        "shells": len(shape.Shells),
        "wires": len(shape.Wires),
    }}

    _output({{
        "status": "ok",
        "object": {repr(object_name)},
        "measurements": measurements,
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def distance_between(filepath, object1, object2, freecad_path=None):
    """Measure minimum distance between two objects.

    Args:
        filepath: Path to .FCStd file.
        object1: Name of first object.
        object2: Name of second object.

    Returns:
        Dict with distance measurement.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj1 = doc.getObject({repr(object1)})
obj2 = doc.getObject({repr(object2)})
if obj1 is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object1)}}})
elif obj2 is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object2)}}})
elif not hasattr(obj1, 'Shape') or not hasattr(obj2, 'Shape'):
    _output({{"status": "error", "error": "Both objects must have shapes"}})
else:
    dist = obj1.Shape.distToShape(obj2.Shape)
    min_dist = dist[0]
    # dist[1] contains the nearest points
    points = dist[1]
    nearest = []
    for pair in points:
        nearest.append({{
            "point1": {{"x": pair[0].x, "y": pair[0].y, "z": pair[0].z}},
            "point2": {{"x": pair[1].x, "y": pair[1].y, "z": pair[1].z}},
        }})

    _output({{
        "status": "ok",
        "object1": {repr(object1)},
        "object2": {repr(object2)},
        "min_distance": min_dist,
        "nearest_points": nearest,
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def bounding_box(filepath, object_name=None, freecad_path=None):
    """Get bounding box for an object or the entire document.

    Args:
        filepath: Path to .FCStd file.
        object_name: Optional object name (None = entire document).

    Returns:
        Dict with bounding box info.
    """
    filepath = os.path.abspath(filepath)

    if object_name:
        code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
elif not hasattr(obj, 'Shape'):
    _output({{"status": "error", "error": "Object has no shape: " + {repr(object_name)}}})
else:
    bb = obj.Shape.BoundBox
    _output({{
        "status": "ok",
        "scope": "object",
        "object": {repr(object_name)},
        "bounds": {{
            "xmin": bb.XMin, "xmax": bb.XMax,
            "ymin": bb.YMin, "ymax": bb.YMax,
            "zmin": bb.ZMin, "zmax": bb.ZMax,
            "diagonal": bb.DiagonalLength,
        }},
        "dimensions": {{"x": bb.XLength, "y": bb.YLength, "z": bb.ZLength}},
    }})
"""
    else:
        code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part
# Compute combined bounding box
xmin = ymin = zmin = float('inf')
xmax = ymax = zmax = float('-inf')
count = 0
for obj in doc.Objects:
    if hasattr(obj, 'Shape') and obj.Shape.Volume > 0:
        bb = obj.Shape.BoundBox
        xmin = min(xmin, bb.XMin)
        ymin = min(ymin, bb.YMin)
        zmin = min(zmin, bb.ZMin)
        xmax = max(xmax, bb.XMax)
        ymax = max(ymax, bb.YMax)
        zmax = max(zmax, bb.ZMax)
        count += 1

if count == 0:
    _output({{"status": "error", "error": "No shape objects in document"}})
else:
    import math
    diag = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2 + (zmax-zmin)**2)
    _output({{
        "status": "ok",
        "scope": "document",
        "shape_count": count,
        "bounds": {{
            "xmin": xmin, "xmax": xmax,
            "ymin": ymin, "ymax": ymax,
            "zmin": zmin, "zmax": zmax,
            "diagonal": diag,
        }},
        "dimensions": {{"x": xmax-xmin, "y": ymax-ymin, "z": zmax-zmin}},
    }})
"""
    return run_script(code, freecad_path=freecad_path)

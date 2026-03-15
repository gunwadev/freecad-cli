"""Object inspection for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def inspect_object(filepath, object_name, freecad_path=None):
    """Get detailed information about a specific object.

    Args:
        filepath: Path to .FCStd file.
        object_name: Name of the object to inspect.

    Returns:
        Dict with detailed object info including properties and shape data.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
else:
    info = {{
        "name": obj.Name,
        "label": obj.Label,
        "type": obj.TypeId,
        "valid": obj.isValid(),
    }}

    # Collect properties
    props = {{}}
    for p in obj.PropertiesList:
        try:
            val = getattr(obj, p)
            if isinstance(val, (int, float, str, bool)):
                props[p] = val
            elif val is None:
                props[p] = None
            elif hasattr(val, 'x') and hasattr(val, 'y') and hasattr(val, 'z'):
                props[p] = {{"x": val.x, "y": val.y, "z": val.z}}
            else:
                props[p] = str(val)
        except Exception:
            props[p] = "<unreadable>"
    info["properties"] = props

    # Shape info if available
    if hasattr(obj, 'Shape'):
        shape = obj.Shape
        bb = shape.BoundBox
        info["shape"] = {{
            "volume": shape.Volume,
            "area": shape.Area,
            "is_valid": shape.isValid(),
            "is_null": shape.isNull(),
            "bounds": {{
                "xmin": bb.XMin, "xmax": bb.XMax,
                "ymin": bb.YMin, "ymax": bb.YMax,
                "zmin": bb.ZMin, "zmax": bb.ZMax,
            }},
            "topology": {{
                "vertices": len(shape.Vertexes),
                "edges": len(shape.Edges),
                "faces": len(shape.Faces),
                "solids": len(shape.Solids),
            }},
        }}
        if hasattr(shape, 'CenterOfMass'):
            com = shape.CenterOfMass
            info["shape"]["center_of_mass"] = {{"x": com.x, "y": com.y, "z": com.z}}

    # Placement
    if hasattr(obj, 'Placement'):
        p = obj.Placement
        info["placement"] = {{
            "position": {{"x": p.Base.x, "y": p.Base.y, "z": p.Base.z}},
            "rotation": {{
                "axis": {{"x": p.Rotation.Axis.x, "y": p.Rotation.Axis.y, "z": p.Rotation.Axis.z}},
                "angle": p.Rotation.Angle,
            }},
        }}

    # Dependencies
    info["in_list"] = [o.Name for o in obj.InList] if obj.InList else []
    info["out_list"] = [o.Name for o in obj.OutList] if obj.OutList else []

    _output({{"status": "ok", "object": info, "filepath": {repr(filepath)}}})
"""
    return run_script(code, freecad_path=freecad_path)


def list_edges(filepath, object_name, freecad_path=None):
    """List edges of a shape object.

    Args:
        filepath: Path to .FCStd file.
        object_name: Name of the object.

    Returns:
        Dict with edge information.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
elif not hasattr(obj, 'Shape'):
    _output({{"status": "error", "error": "Object has no shape"}})
else:
    edges = []
    for i, edge in enumerate(obj.Shape.Edges):
        e = {{
            "index": i + 1,
            "type": edge.Curve.__class__.__name__,
            "length": edge.Length,
        }}
        if hasattr(edge, 'Vertexes') and len(edge.Vertexes) >= 2:
            e["start"] = {{"x": edge.Vertexes[0].X, "y": edge.Vertexes[0].Y, "z": edge.Vertexes[0].Z}}
            e["end"] = {{"x": edge.Vertexes[1].X, "y": edge.Vertexes[1].Y, "z": edge.Vertexes[1].Z}}
        edges.append(e)

    _output({{
        "status": "ok",
        "object": {repr(object_name)},
        "edge_count": len(edges),
        "edges": edges,
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def list_faces(filepath, object_name, freecad_path=None):
    """List faces of a shape object.

    Args:
        filepath: Path to .FCStd file.
        object_name: Name of the object.

    Returns:
        Dict with face information.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
elif not hasattr(obj, 'Shape'):
    _output({{"status": "error", "error": "Object has no shape"}})
else:
    faces = []
    for i, face in enumerate(obj.Shape.Faces):
        f = {{
            "index": i + 1,
            "type": face.Surface.__class__.__name__,
            "area": face.Area,
            "edge_count": len(face.Edges),
        }}
        bb = face.BoundBox
        f["bounds"] = {{
            "xmin": bb.XMin, "xmax": bb.XMax,
            "ymin": bb.YMin, "ymax": bb.YMax,
            "zmin": bb.ZMin, "zmax": bb.ZMax,
        }}
        faces.append(f)

    _output({{
        "status": "ok",
        "object": {repr(object_name)},
        "face_count": len(faces),
        "faces": faces,
    }})
"""
    return run_script(code, freecad_path=freecad_path)

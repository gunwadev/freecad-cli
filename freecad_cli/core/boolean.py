"""Boolean operations for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def _boolean_op(filepath, op_type, name, base_name, tool_name, freecad_path=None):
    """Execute a boolean operation on two shapes.

    Args:
        filepath: Path to .FCStd file.
        op_type: FreeCAD type (Part::Fuse, Part::Cut, Part::Common, Part::Section).
        name: Name for the result object.
        base_name: Name of the base shape.
        tool_name: Name of the tool shape.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part

base = doc.getObject({repr(base_name)})
tool = doc.getObject({repr(tool_name)})
if base is None:
    _output({{"status": "error", "error": "Base object not found: " + {repr(base_name)}}})
elif tool is None:
    _output({{"status": "error", "error": "Tool object not found: " + {repr(tool_name)}}})
else:
    result = doc.addObject({repr(op_type)}, {repr(name)})
    result.Base = base
    result.Tool = tool
    doc.recompute()
    doc.save()

    bb = result.Shape.BoundBox
    _output({{
        "status": "ok",
        "object": {{
            "name": result.Name,
            "label": result.Label,
            "type": result.TypeId,
            "volume": result.Shape.Volume,
            "area": result.Shape.Area,
            "bounds": {{
                "xmin": bb.XMin, "xmax": bb.XMax,
                "ymin": bb.YMin, "ymax": bb.YMax,
                "zmin": bb.ZMin, "zmax": bb.ZMax,
            }},
        }},
        "filepath": {repr(filepath)},
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def fuse(filepath, name, base_name, tool_name, freecad_path=None):
    """Union/fuse two shapes."""
    return _boolean_op(filepath, "Part::Fuse", name, base_name, tool_name, freecad_path)


def cut(filepath, name, base_name, tool_name, freecad_path=None):
    """Subtract tool shape from base shape."""
    return _boolean_op(filepath, "Part::Cut", name, base_name, tool_name, freecad_path)


def common(filepath, name, base_name, tool_name, freecad_path=None):
    """Intersection of two shapes."""
    return _boolean_op(filepath, "Part::Common", name, base_name, tool_name, freecad_path)


def section(filepath, name, base_name, tool_name, freecad_path=None):
    """Section (cross-section) of two shapes."""
    return _boolean_op(filepath, "Part::Section", name, base_name, tool_name, freecad_path)


def multi_fuse(filepath, name, shape_names, freecad_path=None):
    """Fuse multiple shapes together.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the result object.
        shape_names: List of object names to fuse.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part

shapes = []
for sname in {repr(shape_names)}:
    obj = doc.getObject(sname)
    if obj is None:
        _output({{"status": "error", "error": "Object not found: " + repr(sname)}})
        raise SystemExit(1)
    shapes.append(obj)

result = doc.addObject("Part::MultiFuse", {repr(name)})
result.Shapes = shapes
doc.recompute()
doc.save()

bb = result.Shape.BoundBox
_output({{
    "status": "ok",
    "object": {{
        "name": result.Name,
        "label": result.Label,
        "type": result.TypeId,
        "volume": result.Shape.Volume,
        "area": result.Shape.Area,
        "bounds": {{
            "xmin": bb.XMin, "xmax": bb.XMax,
            "ymin": bb.YMin, "ymax": bb.YMax,
            "zmin": bb.ZMin, "zmax": bb.ZMax,
        }},
    }},
    "filepath": {repr(filepath)},
}})
"""
    return run_script(code, freecad_path=freecad_path)

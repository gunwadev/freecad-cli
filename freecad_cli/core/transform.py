"""Transform operations for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def _transform_result(filepath, obj_name):
    """Generate code to output transform result."""
    return f"""
obj = doc.getObject({repr(obj_name)})
p = obj.Placement
bb = obj.Shape.BoundBox
_output({{
    "status": "ok",
    "object": {{
        "name": obj.Name,
        "label": obj.Label,
        "placement": {{
            "position": {{"x": p.Base.x, "y": p.Base.y, "z": p.Base.z}},
            "rotation": {{
                "axis": {{"x": p.Rotation.Axis.x, "y": p.Rotation.Axis.y, "z": p.Rotation.Axis.z}},
                "angle": p.Rotation.Angle,
            }},
        }},
        "bounds": {{
            "xmin": bb.XMin, "xmax": bb.XMax,
            "ymin": bb.YMin, "ymax": bb.YMax,
            "zmin": bb.ZMin, "zmax": bb.ZMax,
        }},
    }},
    "filepath": {repr(filepath)},
}})
"""


def move(filepath, object_name, dx=0, dy=0, dz=0, absolute=False, freecad_path=None):
    """Move an object by a delta or to an absolute position.

    Args:
        filepath: Path to .FCStd file.
        object_name: Name of the object.
        dx, dy, dz: Translation values.
        absolute: If True, set position absolutely instead of delta.
    """
    filepath = os.path.abspath(filepath)

    if absolute:
        move_code = f"""
obj.Placement.Base = FreeCAD.Vector({dx}, {dy}, {dz})
"""
    else:
        move_code = f"""
obj.Placement.Base = obj.Placement.Base + FreeCAD.Vector({dx}, {dy}, {dz})
"""

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
else:
    {move_code.strip()}
    doc.recompute()
    doc.save()
    {_transform_result(filepath, object_name)}
"""
    return run_script(code, freecad_path=freecad_path)


def rotate(filepath, object_name, axis_x=0, axis_y=0, axis_z=1,
           angle=0, freecad_path=None):
    """Rotate an object around an axis.

    Args:
        filepath: Path to .FCStd file.
        object_name: Name of the object.
        axis_x, axis_y, axis_z: Rotation axis.
        angle: Rotation angle in degrees.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
else:
    rot = FreeCAD.Rotation(FreeCAD.Vector({axis_x}, {axis_y}, {axis_z}), {angle})
    obj.Placement.Rotation = rot.multiply(obj.Placement.Rotation)
    doc.recompute()
    doc.save()
    {_transform_result(filepath, object_name)}
"""
    return run_script(code, freecad_path=freecad_path)


def mirror(filepath, name, source_name, plane="XY", freecad_path=None):
    """Mirror an object across a plane.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the mirrored object.
        source_name: Name of the source object.
        plane: Mirror plane ("XY", "XZ", "YZ").
    """
    filepath = os.path.abspath(filepath)

    normal_map = {"XY": "(0,0,1)", "XZ": "(0,1,0)", "YZ": "(1,0,0)"}
    normal = normal_map.get(plane.upper(), "(0,0,1)")

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part

source = doc.getObject({repr(source_name)})
if source is None:
    _output({{"status": "error", "error": "Source object not found: " + {repr(source_name)}}})
else:
    mirror_obj = doc.addObject("Part::Mirroring", {repr(name)})
    mirror_obj.Source = source
    mirror_obj.Normal = FreeCAD.Vector{normal}
    doc.recompute()
    doc.save()
    {_transform_result(filepath, name)}
"""
    return run_script(code, freecad_path=freecad_path)


def copy(filepath, name, source_name, freecad_path=None):
    """Copy an object within the same document.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the copy.
        source_name: Name of the source object.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part

source = doc.getObject({repr(source_name)})
if source is None:
    _output({{"status": "error", "error": "Source object not found: " + {repr(source_name)}}})
else:
    copy_obj = doc.addObject(source.TypeId, {repr(name)})
    copy_obj.Shape = source.Shape.copy()
    copy_obj.Placement = source.Placement
    doc.recompute()
    doc.save()
    {_transform_result(filepath, name)}
"""
    return run_script(code, freecad_path=freecad_path)

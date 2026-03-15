"""Primitive shape creation for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def _add_shape_script(filepath, shape_code, obj_name, freecad_path=None):
    """Common pattern: open doc, add shape, save, return info."""
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part

{shape_code}

doc.recompute()
doc.save()

obj = doc.getObject({repr(obj_name)})
bb = obj.Shape.BoundBox
_output({{
    "status": "ok",
    "object": {{
        "name": obj.Name,
        "label": obj.Label,
        "type": obj.TypeId,
        "volume": obj.Shape.Volume,
        "area": obj.Shape.Area,
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


def add_box(filepath, name, length, width, height,
            x=0, y=0, z=0, freecad_path=None):
    """Add a box primitive to a document.

    Args:
        filepath: Path to .FCStd file.
        name: Object name.
        length, width, height: Box dimensions.
        x, y, z: Position offset.
    """
    shape_code = f"""
obj = doc.addObject("Part::Box", {repr(name)})
obj.Length = {length}
obj.Width = {width}
obj.Height = {height}
obj.Placement.Base = FreeCAD.Vector({x}, {y}, {z})
"""
    return _add_shape_script(filepath, shape_code, name, freecad_path)


def add_cylinder(filepath, name, radius, height,
                 angle=360, x=0, y=0, z=0, freecad_path=None):
    """Add a cylinder primitive to a document."""
    shape_code = f"""
obj = doc.addObject("Part::Cylinder", {repr(name)})
obj.Radius = {radius}
obj.Height = {height}
obj.Angle = {angle}
obj.Placement.Base = FreeCAD.Vector({x}, {y}, {z})
"""
    return _add_shape_script(filepath, shape_code, name, freecad_path)


def add_sphere(filepath, name, radius,
               angle1=-90, angle2=90, angle3=360,
               x=0, y=0, z=0, freecad_path=None):
    """Add a sphere primitive to a document."""
    shape_code = f"""
obj = doc.addObject("Part::Sphere", {repr(name)})
obj.Radius = {radius}
obj.Angle1 = {angle1}
obj.Angle2 = {angle2}
obj.Angle3 = {angle3}
obj.Placement.Base = FreeCAD.Vector({x}, {y}, {z})
"""
    return _add_shape_script(filepath, shape_code, name, freecad_path)


def add_cone(filepath, name, radius1, radius2, height,
             angle=360, x=0, y=0, z=0, freecad_path=None):
    """Add a cone primitive to a document."""
    shape_code = f"""
obj = doc.addObject("Part::Cone", {repr(name)})
obj.Radius1 = {radius1}
obj.Radius2 = {radius2}
obj.Height = {height}
obj.Angle = {angle}
obj.Placement.Base = FreeCAD.Vector({x}, {y}, {z})
"""
    return _add_shape_script(filepath, shape_code, name, freecad_path)


def add_torus(filepath, name, radius1, radius2,
              angle1=-180, angle2=180, angle3=360,
              x=0, y=0, z=0, freecad_path=None):
    """Add a torus primitive to a document."""
    shape_code = f"""
obj = doc.addObject("Part::Torus", {repr(name)})
obj.Radius1 = {radius1}
obj.Radius2 = {radius2}
obj.Angle1 = {angle1}
obj.Angle2 = {angle2}
obj.Angle3 = {angle3}
obj.Placement.Base = FreeCAD.Vector({x}, {y}, {z})
"""
    return _add_shape_script(filepath, shape_code, name, freecad_path)


def add_wedge(filepath, name, xmin, ymin, zmin, x2min, z2min,
              xmax, ymax, zmax, x2max, z2max,
              x=0, y=0, z=0, freecad_path=None):
    """Add a wedge primitive to a document."""
    shape_code = f"""
obj = doc.addObject("Part::Wedge", {repr(name)})
obj.Xmin = {xmin}
obj.Ymin = {ymin}
obj.Zmin = {zmin}
obj.X2min = {x2min}
obj.Z2min = {z2min}
obj.Xmax = {xmax}
obj.Ymax = {ymax}
obj.Zmax = {zmax}
obj.X2max = {x2max}
obj.Z2max = {z2max}
obj.Placement.Base = FreeCAD.Vector({x}, {y}, {z})
"""
    return _add_shape_script(filepath, shape_code, name, freecad_path)

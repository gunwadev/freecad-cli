"""PartDesign operations for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def _pd_result(filepath, obj_name):
    """Generate code for PartDesign result output."""
    return f"""
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


def pad(filepath, name, sketch_name, length, symmetric=False, reversed=False,
        freecad_path=None):
    """Pad (extrude) a sketch to create a solid.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the pad feature.
        sketch_name: Name of the sketch to pad.
        length: Pad length/distance.
        symmetric: If True, pad symmetrically in both directions.
        reversed: If True, pad in the reverse direction.
    """
    filepath = os.path.abspath(filepath)

    type_code = '"Symmetric"' if symmetric else '"Length"'
    rev_code = "True" if reversed else "False"

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import PartDesign

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    # Check if we need a Body
    body = None
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            body = obj
            break
    if body is None:
        body = doc.addObject("PartDesign::Body", "Body")

    # Move sketch into body if needed
    if sketch not in body.Group:
        body.addObject(sketch)

    pad = doc.addObject("PartDesign::Pad", {repr(name)})
    pad.Profile = sketch
    pad.Length = {length}
    pad.Type = {type_code}
    pad.Reversed = {rev_code}
    body.addObject(pad)
    doc.recompute()
    doc.save()
    {_pd_result(filepath, name)}
"""
    return run_script(code, freecad_path=freecad_path)


def pocket(filepath, name, sketch_name, depth, through_all=False,
           freecad_path=None):
    """Create a pocket (subtractive extrusion) from a sketch.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the pocket feature.
        sketch_name: Name of the sketch for the pocket.
        depth: Pocket depth.
        through_all: If True, pocket through the entire solid.
    """
    filepath = os.path.abspath(filepath)

    type_code = '"ThroughAll"' if through_all else '"Length"'

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import PartDesign

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    body = None
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            body = obj
            break
    if body is None:
        _output({{"status": "error", "error": "No PartDesign Body found"}})
    else:
        if sketch not in body.Group:
            body.addObject(sketch)
        pocket = doc.addObject("PartDesign::Pocket", {repr(name)})
        pocket.Profile = sketch
        pocket.Length = {depth}
        pocket.Type = {type_code}
        body.addObject(pocket)
        doc.recompute()
        doc.save()
        {_pd_result(filepath, name)}
"""
    return run_script(code, freecad_path=freecad_path)


def revolve(filepath, name, sketch_name, angle=360, axis="Y",
            freecad_path=None):
    """Revolve a sketch around an axis.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the revolution feature.
        sketch_name: Name of the sketch to revolve.
        angle: Revolution angle in degrees.
        axis: Revolution axis ("X", "Y", "Z").
    """
    filepath = os.path.abspath(filepath)

    axis_map = {
        "X": "(1, 0, 0)",
        "Y": "(0, 1, 0)",
        "Z": "(0, 0, 1)",
    }
    axis_vec = axis_map.get(axis.upper(), "(0, 1, 0)")

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import PartDesign

sketch = doc.getObject({repr(sketch_name)})
if sketch is None:
    _output({{"status": "error", "error": "Sketch not found: " + {repr(sketch_name)}}})
else:
    body = None
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            body = obj
            break
    if body is None:
        body = doc.addObject("PartDesign::Body", "Body")

    if sketch not in body.Group:
        body.addObject(sketch)

    rev = doc.addObject("PartDesign::Revolution", {repr(name)})
    rev.Profile = sketch
    rev.Angle = {angle}
    rev.Axis = {axis_vec}
    body.addObject(rev)
    doc.recompute()
    doc.save()
    {_pd_result(filepath, name)}
"""
    return run_script(code, freecad_path=freecad_path)


def fillet(filepath, name, base_name, edge_indices, radius, freecad_path=None):
    """Apply fillet (rounding) to edges of an object.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the fillet feature.
        base_name: Name of the base object.
        edge_indices: List of edge indices (1-based) to fillet.
        radius: Fillet radius.
    """
    filepath = os.path.abspath(filepath)

    edges = [f'"Edge{i}"' for i in edge_indices]
    edges_str = "[" + ", ".join(edges) + "]"

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import PartDesign

base = doc.getObject({repr(base_name)})
if base is None:
    _output({{"status": "error", "error": "Base object not found: " + {repr(base_name)}}})
else:
    body = None
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            body = obj
            break
    if body is None:
        body = doc.addObject("PartDesign::Body", "Body")

    fillet = doc.addObject("PartDesign::Fillet", {repr(name)})
    fillet.Base = (base, {edges_str})
    fillet.Radius = {radius}
    body.addObject(fillet)
    doc.recompute()
    doc.save()
    {_pd_result(filepath, name)}
"""
    return run_script(code, freecad_path=freecad_path)


def chamfer(filepath, name, base_name, edge_indices, size, freecad_path=None):
    """Apply chamfer to edges of an object.

    Args:
        filepath: Path to .FCStd file.
        name: Name for the chamfer feature.
        base_name: Name of the base object.
        edge_indices: List of edge indices (1-based) to chamfer.
        size: Chamfer size.
    """
    filepath = os.path.abspath(filepath)

    edges = [f'"Edge{i}"' for i in edge_indices]
    edges_str = "[" + ", ".join(edges) + "]"

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import PartDesign

base = doc.getObject({repr(base_name)})
if base is None:
    _output({{"status": "error", "error": "Base object not found: " + {repr(base_name)}}})
else:
    body = None
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            body = obj
            break
    if body is None:
        body = doc.addObject("PartDesign::Body", "Body")

    chamfer = doc.addObject("PartDesign::Chamfer", {repr(name)})
    chamfer.Base = (base, {edges_str})
    chamfer.Size = {size}
    body.addObject(chamfer)
    doc.recompute()
    doc.save()
    {_pd_result(filepath, name)}
"""
    return run_script(code, freecad_path=freecad_path)

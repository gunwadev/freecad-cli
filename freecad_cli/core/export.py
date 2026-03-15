"""Export operations for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


SUPPORTED_FORMATS = {
    "step": {"extensions": [".step", ".stp"], "module": "Part"},
    "iges": {"extensions": [".iges", ".igs"], "module": "Part"},
    "stl": {"extensions": [".stl"], "module": "Mesh"},
    "brep": {"extensions": [".brep", ".brp"], "module": "Part"},
    "obj": {"extensions": [".obj"], "module": "Mesh"},
    "dae": {"extensions": [".dae"], "module": "importDAE"},
    "dxf": {"extensions": [".dxf"], "module": "importDXF"},
    "svg": {"extensions": [".svg"], "module": "importSVG"},
}


def export_object(filepath, output_path, object_names=None,
                  format=None, freecad_path=None):
    """Export objects from a FreeCAD document to a file format.

    Args:
        filepath: Path to .FCStd source document.
        output_path: Path for the exported file.
        object_names: List of object names to export (None = all).
        format: Export format (auto-detected from extension if None).

    Returns:
        Dict with export result.
    """
    filepath = os.path.abspath(filepath)
    output_path = os.path.abspath(output_path)

    ext = os.path.splitext(output_path)[1].lower()

    # Build object selection code
    if object_names:
        obj_select = f"""
objects = []
for n in {repr(object_names)}:
    obj = doc.getObject(n)
    if obj is None:
        _output({{"status": "error", "error": "Object not found: " + repr(n)}})
        raise SystemExit(1)
    objects.append(obj)
"""
    else:
        obj_select = """
objects = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
if not objects:
    objects = doc.Objects
"""

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part

{obj_select}

if not objects:
    _output({{"status": "error", "error": "No objects to export"}})
else:
    # Use FreeCAD's import/export system
    import importlib
    ext = {repr(ext)}

    if ext in ('.step', '.stp'):
        Part.export(objects, {repr(output_path)})
    elif ext in ('.iges', '.igs'):
        Part.export(objects, {repr(output_path)})
    elif ext in ('.brep', '.brp'):
        if len(objects) == 1 and hasattr(objects[0], 'Shape'):
            objects[0].Shape.exportBrep({repr(output_path)})
        else:
            Part.export(objects, {repr(output_path)})
    elif ext == '.stl':
        import Mesh
        shapes = []
        for obj in objects:
            if hasattr(obj, 'Shape'):
                shapes.append(obj)
        Mesh.export(shapes, {repr(output_path)})
    elif ext == '.obj':
        import Mesh
        shapes = []
        for obj in objects:
            if hasattr(obj, 'Shape'):
                shapes.append(obj)
        Mesh.export(shapes, {repr(output_path)})
    else:
        # Try generic export
        FreeCAD.loadFile = None  # safety
        Part.export(objects, {repr(output_path)})

    import os as _os
    size = _os.path.getsize({repr(output_path)})
    _output({{
        "status": "ok",
        "output": {repr(output_path)},
        "format": ext.lstrip('.'),
        "objects_exported": len(objects),
        "file_size_bytes": size,
    }})
"""
    return run_script(code, freecad_path=freecad_path)


def export_all(filepath, output_path, format=None, freecad_path=None):
    """Export all shape objects from a document."""
    return export_object(filepath, output_path, object_names=None,
                         format=format, freecad_path=freecad_path)


def list_formats(freecad_path=None):
    """List supported export formats.

    Returns:
        Dict with format information.
    """
    return {
        "status": "ok",
        "formats": [
            {"name": name, "extensions": info["extensions"]}
            for name, info in SUPPORTED_FORMATS.items()
        ],
    }


def import_file(filepath, input_path, freecad_path=None):
    """Import a file into a FreeCAD document.

    Args:
        filepath: Path to .FCStd document to import into.
        input_path: Path to the file to import.

    Returns:
        Dict with import result.
    """
    filepath = os.path.abspath(filepath)
    input_path = os.path.abspath(input_path)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
import Part
import Import

before = set(obj.Name for obj in doc.Objects)
Import.insert({repr(input_path)}, doc.Name)
doc.recompute()
after = set(obj.Name for obj in doc.Objects)
new_objects = after - before

doc.save()

_output({{
    "status": "ok",
    "imported_from": {repr(input_path)},
    "new_objects": list(new_objects),
    "total_objects": len(doc.Objects),
    "filepath": {repr(filepath)},
}})
"""
    return run_script(code, freecad_path=freecad_path)

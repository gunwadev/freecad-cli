"""Document/project management for FreeCAD CLI harness."""

import os

from freecad_cli.utils.runner import run_script


def new_document(filepath, label=None, freecad_path=None):
    """Create a new FreeCAD document and save it.

    Args:
        filepath: Path to save the .FCStd file.
        label: Optional document label.

    Returns:
        Dict with document info.
    """
    filepath = os.path.abspath(filepath)
    name = os.path.splitext(os.path.basename(filepath))[0]
    label_arg = repr(label) if label else repr(name)

    code = f"""
doc = FreeCAD.newDocument({repr(name)})
doc.Label = {label_arg}
doc.saveAs({repr(filepath)})
_output({{
    "status": "ok",
    "document": {{
        "name": doc.Name,
        "label": doc.Label,
        "filepath": {repr(filepath)},
        "objects": 0,
    }}
}})
"""
    return run_script(code, freecad_path=freecad_path)


def open_document(filepath, freecad_path=None):
    """Open an existing FreeCAD document.

    Args:
        filepath: Path to .FCStd file.

    Returns:
        Dict with document info.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
objs = []
for obj in doc.Objects:
    objs.append({{
        "name": obj.Name,
        "label": obj.Label,
        "type": obj.TypeId,
    }})
_output({{
    "status": "ok",
    "document": {{
        "name": doc.Name,
        "label": doc.Label,
        "filepath": doc.FileName,
        "objects": len(objs),
        "object_list": objs,
    }}
}})
"""
    return run_script(code, freecad_path=freecad_path)


def document_info(filepath, freecad_path=None):
    """Get detailed info about a FreeCAD document.

    Args:
        filepath: Path to .FCStd file.

    Returns:
        Dict with detailed document info.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
objs = []
for obj in doc.Objects:
    props = {{}}
    for p in obj.PropertiesList:
        try:
            val = getattr(obj, p)
            if isinstance(val, (int, float, str, bool)):
                props[p] = val
            elif hasattr(val, 'x') and hasattr(val, 'y') and hasattr(val, 'z'):
                props[p] = {{"x": val.x, "y": val.y, "z": val.z}}
            else:
                props[p] = str(val)
        except Exception:
            props[p] = "<unreadable>"
    objs.append({{
        "name": obj.Name,
        "label": obj.Label,
        "type": obj.TypeId,
        "valid": obj.isValid(),
        "properties": props,
    }})
_output({{
    "status": "ok",
    "document": {{
        "name": doc.Name,
        "label": doc.Label,
        "filepath": doc.FileName,
        "object_count": len(objs),
        "objects": objs,
    }}
}})
"""
    return run_script(code, freecad_path=freecad_path)


def save_document(filepath, save_as=None, freecad_path=None):
    """Save a FreeCAD document.

    Args:
        filepath: Path to the open .FCStd file.
        save_as: Optional new path (save-as).

    Returns:
        Dict with save result.
    """
    filepath = os.path.abspath(filepath)

    if save_as:
        save_as = os.path.abspath(save_as)
        code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
doc.saveAs({repr(save_as)})
_output({{"status": "ok", "filepath": {repr(save_as)}}})
"""
    else:
        code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
doc.save()
_output({{"status": "ok", "filepath": {repr(filepath)}}})
"""
    return run_script(code, freecad_path=freecad_path)


def list_objects(filepath, type_filter=None, freecad_path=None):
    """List objects in a FreeCAD document.

    Args:
        filepath: Path to .FCStd file.
        type_filter: Optional type filter (e.g., "Part::Feature").

    Returns:
        Dict with object list.
    """
    filepath = os.path.abspath(filepath)
    filter_code = ""
    if type_filter:
        filter_code = f"""
    if {repr(type_filter)} not in obj.TypeId:
        continue"""

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
objs = []
for obj in doc.Objects:{filter_code}
    objs.append({{
        "name": obj.Name,
        "label": obj.Label,
        "type": obj.TypeId,
    }})
_output({{"status": "ok", "objects": objs, "count": len(objs)}})
"""
    return run_script(code, freecad_path=freecad_path)


def delete_object(filepath, object_name, freecad_path=None):
    """Delete an object from a FreeCAD document.

    Args:
        filepath: Path to .FCStd file.
        object_name: Name of the object to delete.

    Returns:
        Dict with result.
    """
    filepath = os.path.abspath(filepath)

    code = f"""
doc = FreeCAD.openDocument({repr(filepath)})
obj = doc.getObject({repr(object_name)})
if obj is None:
    _output({{"status": "error", "error": "Object not found: " + {repr(object_name)}}})
else:
    doc.removeObject({repr(object_name)})
    doc.recompute()
    doc.save()
    _output({{"status": "ok", "deleted": {repr(object_name)}, "filepath": {repr(filepath)}}})
"""
    return run_script(code, freecad_path=freecad_path)

"""FreeCAD session management - handles FreeCADCmd discovery and version info."""

from freecad_cli.utils.runner import find_freecad_cmd, run_script


def get_version(freecad_path=None):
    """Get FreeCAD version information.

    Returns:
        Dict with version details.
    """
    code = """
version = FreeCAD.Version()
_output({
    "status": "ok",
    "version": {
        "major": version[0],
        "minor": version[1],
        "patch": version[2],
        "build": version[3] if len(version) > 3 else "",
        "string": ".".join(version[:3]),
    }
})
"""
    return run_script(code, freecad_path=freecad_path)


def check_health(freecad_path=None):
    """Check if FreeCAD is available and working.

    Returns:
        Dict with health status.
    """
    try:
        cmd_path = find_freecad_cmd(freecad_path)
        version_info = get_version(freecad_path)
        return {
            "status": "ok",
            "freecad_cmd": cmd_path,
            "version": version_info.get("version", {}),
            "healthy": True,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "healthy": False,
        }


def list_modules(freecad_path=None):
    """List available FreeCAD modules/workbenches.

    Returns:
        Dict with list of available modules.
    """
    code = """
import os
mod_dir = os.path.join(FreeCAD.getHomePath(), "Mod")
modules = []
if os.path.isdir(mod_dir):
    for name in sorted(os.listdir(mod_dir)):
        full = os.path.join(mod_dir, name)
        if os.path.isdir(full):
            has_init = os.path.isfile(os.path.join(full, "Init.py"))
            modules.append({"name": name, "initialized": has_init})
_output({"status": "ok", "modules": modules})
"""
    return run_script(code, freecad_path=freecad_path)

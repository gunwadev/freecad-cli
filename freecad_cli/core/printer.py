"""Printer profile management for freecad-cli."""

import json
import os

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".printers")
PROFILES_FILE = os.path.join(CONFIG_DIR, "printers.json")


def _ensure_config():
    """Ensure config directory and file exist."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.isfile(PROFILES_FILE):
        _save_profiles({"default": None, "printers": {}})


def _load_profiles():
    """Load printer profiles from disk."""
    _ensure_config()
    with open(PROFILES_FILE, "r") as f:
        return json.load(f)


def _save_profiles(data):
    """Save printer profiles to disk."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(PROFILES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_printer(name, model=None, bed_x=None, bed_y=None, bed_z=None,
                nozzle=0.4, materials=None, heated_bed=True, notes=None):
    """Add or update a printer profile.

    Args:
        name: Short name for the printer (e.g., "ender3", "prusa-mk4").
        model: Full model name (e.g., "Creality Ender 3 V2").
        bed_x: Build volume X in mm.
        bed_y: Build volume Y in mm.
        bed_z: Build volume Z in mm.
        nozzle: Nozzle diameter in mm (default 0.4).
        materials: List of supported materials (e.g., ["PLA", "PETG", "TPU"]).
        heated_bed: Whether the printer has a heated bed.
        notes: Any extra notes about the printer.

    Returns:
        Dict with result.
    """
    profiles = _load_profiles()

    printer = {
        "model": model or name,
        "bed_size_mm": {
            "x": bed_x,
            "y": bed_y,
            "z": bed_z,
        },
        "nozzle_mm": nozzle,
        "materials": materials or ["PLA"],
        "heated_bed": heated_bed,
        "notes": notes,
    }

    profiles["printers"][name] = printer

    # Set as default if it's the first printer
    if profiles["default"] is None:
        profiles["default"] = name

    _save_profiles(profiles)

    return {
        "status": "ok",
        "action": "added",
        "printer": name,
        "profile": printer,
        "is_default": profiles["default"] == name,
    }


def remove_printer(name):
    """Remove a printer profile."""
    profiles = _load_profiles()

    if name not in profiles["printers"]:
        return {"status": "error", "error": f"Printer not found: {name}"}

    del profiles["printers"][name]

    if profiles["default"] == name:
        remaining = list(profiles["printers"].keys())
        profiles["default"] = remaining[0] if remaining else None

    _save_profiles(profiles)

    return {"status": "ok", "action": "removed", "printer": name}


def list_printers():
    """List all printer profiles."""
    profiles = _load_profiles()

    return {
        "status": "ok",
        "default": profiles["default"],
        "printers": profiles["printers"],
        "count": len(profiles["printers"]),
    }


def get_printer(name=None):
    """Get a specific printer profile, or the default.

    Args:
        name: Printer name. If None, returns the default printer.

    Returns:
        Dict with printer profile.
    """
    profiles = _load_profiles()

    if name is None:
        name = profiles["default"]

    if name is None:
        return {"status": "error", "error": "No printers configured. Run: freecad-cli printer add"}

    if name not in profiles["printers"]:
        return {"status": "error", "error": f"Printer not found: {name}"}

    return {
        "status": "ok",
        "printer": name,
        "is_default": profiles["default"] == name,
        "profile": profiles["printers"][name],
    }


def set_default(name):
    """Set the default printer."""
    profiles = _load_profiles()

    if name not in profiles["printers"]:
        return {"status": "error", "error": f"Printer not found: {name}"}

    profiles["default"] = name
    _save_profiles(profiles)

    return {"status": "ok", "action": "set_default", "printer": name}


def get_print_settings(name=None):
    """Get recommended print settings based on the printer profile.

    Returns settings the AI/user should use for slicing.
    """
    result = get_printer(name)
    if result["status"] != "ok":
        return result

    profile = result["profile"]
    nozzle = profile["nozzle_mm"]
    materials = profile["materials"]

    settings = {
        "printer": result["printer"],
        "bed_size_mm": profile["bed_size_mm"],
        "nozzle_mm": nozzle,
        "recommended_layer_heights": {
            "draft": round(nozzle * 0.75, 2),
            "normal": round(nozzle * 0.5, 2),
            "fine": round(nozzle * 0.25, 2),
        },
        "max_print_size_mm": profile["bed_size_mm"],
        "supported_materials": materials,
        "heated_bed": profile["heated_bed"],
    }

    if profile.get("notes"):
        settings["notes"] = profile["notes"]

    return {"status": "ok", "settings": settings}

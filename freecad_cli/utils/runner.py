"""FreeCAD script runner - executes Python scripts via FreeCADCmd."""

import os
import shutil
import subprocess
import tempfile

from freecad_cli.utils.errors import (
    FreeCADNotFoundError,
    ScriptExecutionError,
)
from freecad_cli.utils.json_output import extract_json, wrap_json


# Common search paths for FreeCADCmd on different platforms
_FREECAD_SEARCH_PATHS = [
    # macOS (both capitalized and lowercase variants)
    "/Applications/FreeCAD.app/Contents/Resources/bin/FreeCADCmd",
    "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd",
    "/Applications/FreeCAD.app/Contents/bin/FreeCADCmd",
    "/Applications/FreeCAD.app/Contents/bin/freecadcmd",
    os.path.expanduser("~/Applications/FreeCAD.app/Contents/Resources/bin/FreeCADCmd"),
    os.path.expanduser("~/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"),
    # Linux
    "/usr/bin/FreeCADCmd",
    "/usr/bin/freecadcmd",
    "/usr/local/bin/FreeCADCmd",
    "/usr/local/bin/freecadcmd",
    "/snap/freecad/current/usr/bin/FreeCADCmd",
    # Flatpak
    "/var/lib/flatpak/exports/bin/org.freecadweb.FreeCAD.Cmd",
    # conda/mamba
    os.path.expanduser("~/miniconda3/bin/FreeCADCmd"),
    os.path.expanduser("~/anaconda3/bin/FreeCADCmd"),
]


def find_freecad_cmd(custom_path=None):
    """Find the FreeCADCmd executable.

    Args:
        custom_path: Optional explicit path to FreeCADCmd.

    Returns:
        Absolute path to FreeCADCmd executable.

    Raises:
        FreeCADNotFoundError: If FreeCADCmd cannot be found.
    """
    if custom_path:
        if os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
            return os.path.abspath(custom_path)
        raise FreeCADNotFoundError(f"FreeCADCmd not found at: {custom_path}")

    # Check PATH first (both capitalized and lowercase)
    for name in ("FreeCADCmd", "freecadcmd"):
        which = shutil.which(name)
        if which:
            return which

    # Check FREECAD_CMD env var
    env_path = os.environ.get("FREECAD_CMD")
    if env_path and os.path.isfile(env_path):
        return env_path

    # Search common locations
    for path in _FREECAD_SEARCH_PATHS:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    raise FreeCADNotFoundError(
        "FreeCADCmd not found. Install FreeCAD or set FREECAD_CMD environment variable."
    )


def build_script(code, result_expr=None):
    """Build a complete FreeCAD script with JSON output wrapper.

    Args:
        code: Python code to execute within FreeCAD.
        result_expr: Optional expression whose value becomes the JSON result.
                     If None, the code should print the JSON markers itself.

    Returns:
        Complete script string.
    """
    lines = [
        "import sys",
        "import json",
        "import FreeCAD",
        "",
        "JSON_START = '__CLI_JSON__'",
        "JSON_END = '__CLI_JSON_END__'",
        "",
        "def _output(data):",
        "    print(JSON_START + json.dumps(data) + JSON_END)",
        "",
        "try:",
    ]
    # Indent the user code
    for line in code.strip().split("\n"):
        lines.append(f"    {line}")

    if result_expr:
        lines.append(f"    _output({result_expr})")

    lines.extend([
        "except Exception as _e:",
        '    _output({"status": "error", "error": str(_e), "type": type(_e).__name__})',
    ])

    return "\n".join(lines) + "\n"


def run_script(code, result_expr=None, freecad_path=None, timeout=120):
    """Execute a FreeCAD Python script and return the JSON result.

    Args:
        code: Python code to execute.
        result_expr: Optional expression for the result.
        freecad_path: Optional path to FreeCADCmd.
        timeout: Timeout in seconds.

    Returns:
        Dict with the script's JSON output.

    Raises:
        ScriptExecutionError: If the script fails.
        FreeCADNotFoundError: If FreeCADCmd is not found.
    """
    freecad_cmd = find_freecad_cmd(freecad_path)
    script = build_script(code, result_expr)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="freecad_cli_", delete=False
    ) as f:
        f.write(script)
        script_path = f.name

    try:
        result = subprocess.run(
            [freecad_cmd, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Extract JSON from stdout
        data = extract_json(result.stdout)
        if data is not None:
            if data.get("status") == "error":
                raise ScriptExecutionError(
                    data.get("error", "Unknown error"),
                    stderr=result.stderr,
                    returncode=result.returncode,
                )
            return data

        # No JSON output found - check for errors
        if result.returncode != 0:
            raise ScriptExecutionError(
                f"FreeCADCmd exited with code {result.returncode}",
                stderr=result.stderr,
                returncode=result.returncode,
            )

        raise ScriptExecutionError(
            "No JSON output from FreeCAD script",
            stderr=result.stderr,
            returncode=result.returncode,
        )

    except subprocess.TimeoutExpired:
        raise ScriptExecutionError(f"Script timed out after {timeout}s")

    finally:
        os.unlink(script_path)


def run_script_raw(code, freecad_path=None, timeout=120):
    """Execute a FreeCAD Python script and return raw stdout/stderr.

    Args:
        code: Python code to execute.
        freecad_path: Optional path to FreeCADCmd.
        timeout: Timeout in seconds.

    Returns:
        Tuple of (stdout, stderr, returncode).
    """
    freecad_cmd = find_freecad_cmd(freecad_path)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="freecad_cli_", delete=False
    ) as f:
        f.write(code)
        script_path = f.name

    try:
        result = subprocess.run(
            [freecad_cmd, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        raise ScriptExecutionError(f"Script timed out after {timeout}s")
    finally:
        os.unlink(script_path)

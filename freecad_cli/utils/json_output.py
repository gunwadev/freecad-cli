"""JSON output formatting for FreeCAD CLI harness."""

import json
import sys


# Markers used to extract JSON from FreeCAD's stdout
JSON_START = "__CLI_JSON__"
JSON_END = "__CLI_JSON_END__"


def wrap_json(data):
    """Wrap data dict with markers for extraction from FreeCAD stdout."""
    return f"{JSON_START}{json.dumps(data)}{JSON_END}"


def extract_json(output):
    """Extract JSON data from FreeCAD stdout containing markers."""
    start = output.find(JSON_START)
    end = output.find(JSON_END)
    if start == -1 or end == -1:
        return None
    json_str = output[start + len(JSON_START):end]
    return json.loads(json_str)


def format_output(data, json_mode=False):
    """Format output for display. Returns string."""
    if json_mode:
        return json.dumps(data, indent=2)
    return _format_human(data)


def _format_human(data):
    """Format data for human-readable output."""
    if isinstance(data, dict):
        if "error" in data:
            return f"Error: {data['error']}"
        if "status" in data and data["status"] == "ok":
            lines = []
            for key, value in data.items():
                if key == "status":
                    continue
                if isinstance(value, list):
                    lines.append(f"{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            parts = [f"{k}={v}" for k, v in item.items()]
                            lines.append(f"  - {', '.join(parts)}")
                        else:
                            lines.append(f"  - {item}")
                elif isinstance(value, dict):
                    lines.append(f"{key}:")
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines) if lines else "OK"
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    return str(data)


def print_result(data, json_mode=False, file=None):
    """Print formatted result to stdout or specified file."""
    output = format_output(data, json_mode)
    print(output, file=file or sys.stdout)

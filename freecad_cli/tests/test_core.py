"""Unit tests for FreeCAD CLI harness core modules.

These tests verify module logic using mocked FreeCAD execution.
No actual FreeCAD installation required.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from freecad_cli.utils.json_output import (
    wrap_json,
    extract_json,
    format_output,
    JSON_START,
    JSON_END,
)
from freecad_cli.utils.runner import build_script, find_freecad_cmd
from freecad_cli.utils.errors import (
    FreeCADNotFoundError,
    ScriptExecutionError,
    DocumentError,
    ExportError,
    GeometryError,
)


# ============================================================
# JSON Output Tests
# ============================================================

class TestJsonOutput(unittest.TestCase):
    """Tests for JSON output formatting."""

    def test_wrap_json_produces_markers(self):
        data = {"status": "ok", "value": 42}
        result = wrap_json(data)
        self.assertIn(JSON_START, result)
        self.assertIn(JSON_END, result)
        self.assertIn('"status": "ok"', result)

    def test_extract_json_valid(self):
        data = {"status": "ok", "count": 3}
        wrapped = f"some noise {JSON_START}{json.dumps(data)}{JSON_END} more noise"
        extracted = extract_json(wrapped)
        self.assertEqual(extracted["status"], "ok")
        self.assertEqual(extracted["count"], 3)

    def test_extract_json_no_markers(self):
        result = extract_json("just regular output with no markers")
        self.assertIsNone(result)

    def test_extract_json_partial_markers(self):
        result = extract_json(f"{JSON_START}{{\"key\": \"value\"}} no end marker")
        self.assertIsNone(result)

    def test_format_output_json_mode(self):
        data = {"status": "ok", "name": "Box"}
        result = format_output(data, json_mode=True)
        parsed = json.loads(result)
        self.assertEqual(parsed["name"], "Box")

    def test_format_output_human_mode(self):
        data = {"status": "ok", "name": "Box", "volume": 1000.0}
        result = format_output(data, json_mode=False)
        self.assertIn("name: Box", result)
        self.assertIn("volume: 1000.0", result)
        self.assertNotIn("status:", result)  # status: ok is hidden

    def test_format_output_error(self):
        data = {"error": "Something went wrong"}
        result = format_output(data, json_mode=False)
        self.assertIn("Error: Something went wrong", result)

    def test_format_output_list_values(self):
        data = {
            "status": "ok",
            "objects": [
                {"name": "Box", "type": "Part::Box"},
                {"name": "Cyl", "type": "Part::Cylinder"},
            ],
        }
        result = format_output(data, json_mode=False)
        self.assertIn("objects:", result)
        self.assertIn("name=Box", result)

    def test_format_output_dict_values(self):
        data = {
            "status": "ok",
            "bounds": {"xmin": 0, "xmax": 10},
        }
        result = format_output(data, json_mode=False)
        self.assertIn("bounds:", result)
        self.assertIn("xmin: 0", result)

    def test_wrap_then_extract_roundtrip(self):
        data = {"status": "ok", "nested": {"a": [1, 2, 3]}}
        wrapped = wrap_json(data)
        extracted = extract_json(wrapped)
        self.assertEqual(extracted, data)


# ============================================================
# Runner Tests
# ============================================================

class TestRunner(unittest.TestCase):
    """Tests for script runner module."""

    def test_build_script_basic(self):
        code = "result = 42"
        script = build_script(code)
        self.assertIn("import FreeCAD", script)
        self.assertIn("import json", script)
        self.assertIn("result = 42", script)
        self.assertIn("JSON_START", script)
        self.assertIn("except Exception", script)

    def test_build_script_with_result_expr(self):
        code = "x = 42"
        script = build_script(code, result_expr='{"value": x}')
        self.assertIn("_output({\"value\": x})", script)

    def test_build_script_error_handling(self):
        code = "raise ValueError('test')"
        script = build_script(code)
        self.assertIn("except Exception as _e:", script)
        self.assertIn('"status": "error"', script)

    def test_build_script_indentation(self):
        code = "a = 1\nb = 2\nc = a + b"
        script = build_script(code)
        # All user code should be indented inside try block
        lines = script.split("\n")
        try_found = False
        for line in lines:
            if line.strip() == "try:":
                try_found = True
            elif try_found and line.strip() and not line.startswith("except"):
                self.assertTrue(line.startswith("    "),
                                f"Line not indented in try block: {repr(line)}")
                break

    def test_find_freecad_cmd_custom_path_exists(self):
        with tempfile.NamedTemporaryFile(suffix="_FreeCADCmd", delete=False) as f:
            f.write(b"#!/bin/sh\n")
            path = f.name
        try:
            os.chmod(path, 0o755)
            result = find_freecad_cmd(custom_path=path)
            self.assertEqual(result, os.path.abspath(path))
        finally:
            os.unlink(path)

    def test_find_freecad_cmd_custom_path_missing(self):
        with self.assertRaises(FreeCADNotFoundError):
            find_freecad_cmd(custom_path="/nonexistent/path/FreeCADCmd")

    def test_find_freecad_cmd_not_found_anywhere(self):
        """Test that FreeCADNotFoundError is raised when no FreeCADCmd exists."""
        with patch("shutil.which", return_value=None), \
             patch.dict(os.environ, {}, clear=True), \
             patch("os.path.isfile", return_value=False):
            with self.assertRaises(FreeCADNotFoundError):
                find_freecad_cmd()


# ============================================================
# Error Type Tests
# ============================================================

class TestErrors(unittest.TestCase):
    """Tests for error types."""

    def test_freecad_not_found_error(self):
        e = FreeCADNotFoundError("not found")
        self.assertIsInstance(e, Exception)
        self.assertEqual(str(e), "not found")

    def test_script_execution_error(self):
        e = ScriptExecutionError("failed", stderr="error output", returncode=1)
        self.assertEqual(str(e), "failed")
        self.assertEqual(e.stderr, "error output")
        self.assertEqual(e.returncode, 1)

    def test_document_error(self):
        e = DocumentError("bad doc")
        self.assertIsInstance(e, Exception)

    def test_export_error(self):
        e = ExportError("export failed")
        self.assertIsInstance(e, Exception)

    def test_geometry_error(self):
        e = GeometryError("bad geometry")
        self.assertIsInstance(e, Exception)


# ============================================================
# Project Module Script Generation Tests
# ============================================================

class TestProjectScriptGeneration(unittest.TestCase):
    """Tests that project module generates correct FreeCAD scripts."""

    @patch("freecad_cli.core.project.run_script")
    def test_new_document_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.project import new_document
        new_document("/tmp/test.FCStd", label="Test")
        mock_run.assert_called_once()
        code = mock_run.call_args[0][0]
        self.assertIn("FreeCAD.newDocument", code)
        self.assertIn("saveAs", code)
        self.assertIn("/tmp/test.FCStd", code)
        self.assertIn("'Test'", code)

    @patch("freecad_cli.core.project.run_script")
    def test_open_document_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.project import open_document
        open_document("/tmp/test.FCStd")
        code = mock_run.call_args[0][0]
        self.assertIn("FreeCAD.openDocument", code)
        self.assertIn("/tmp/test.FCStd", code)

    @patch("freecad_cli.core.project.run_script")
    def test_document_info_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.project import document_info
        document_info("/tmp/test.FCStd")
        code = mock_run.call_args[0][0]
        self.assertIn("PropertiesList", code)
        self.assertIn("isValid()", code)

    @patch("freecad_cli.core.project.run_script")
    def test_list_objects_with_filter(self, mock_run):
        mock_run.return_value = {"status": "ok", "objects": []}
        from freecad_cli.core.project import list_objects
        list_objects("/tmp/test.FCStd", type_filter="Part::Feature")
        code = mock_run.call_args[0][0]
        self.assertIn("Part::Feature", code)

    @patch("freecad_cli.core.project.run_script")
    def test_delete_object_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.project import delete_object
        delete_object("/tmp/test.FCStd", "MyBox")
        code = mock_run.call_args[0][0]
        self.assertIn("removeObject", code)
        self.assertIn("'MyBox'", code)


# ============================================================
# Primitives Module Script Generation Tests
# ============================================================

class TestPrimitivesScriptGeneration(unittest.TestCase):
    """Tests that primitives module generates correct FreeCAD scripts."""

    @patch("freecad_cli.core.primitives.run_script")
    def test_add_box_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.primitives import add_box
        add_box("/tmp/test.FCStd", "MyBox", 10, 20, 30)
        code = mock_run.call_args[0][0]
        self.assertIn("Part::Box", code)
        self.assertIn("'MyBox'", code)
        self.assertIn("Length = 10", code)
        self.assertIn("Width = 20", code)
        self.assertIn("Height = 30", code)

    @patch("freecad_cli.core.primitives.run_script")
    def test_add_cylinder_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.primitives import add_cylinder
        add_cylinder("/tmp/test.FCStd", "MyCyl", 5, 15)
        code = mock_run.call_args[0][0]
        self.assertIn("Part::Cylinder", code)
        self.assertIn("Radius = 5", code)
        self.assertIn("Height = 15", code)

    @patch("freecad_cli.core.primitives.run_script")
    def test_add_sphere_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.primitives import add_sphere
        add_sphere("/tmp/test.FCStd", "MySphere", 7.5)
        code = mock_run.call_args[0][0]
        self.assertIn("Part::Sphere", code)
        self.assertIn("Radius = 7.5", code)

    @patch("freecad_cli.core.primitives.run_script")
    def test_add_cone_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.primitives import add_cone
        add_cone("/tmp/test.FCStd", "MyCone", 10, 3, 20)
        code = mock_run.call_args[0][0]
        self.assertIn("Part::Cone", code)
        self.assertIn("Radius1 = 10", code)
        self.assertIn("Radius2 = 3", code)
        self.assertIn("Height = 20", code)

    @patch("freecad_cli.core.primitives.run_script")
    def test_add_box_with_position(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.primitives import add_box
        add_box("/tmp/test.FCStd", "Box2", 10, 20, 30, x=5, y=10, z=15)
        code = mock_run.call_args[0][0]
        self.assertIn("FreeCAD.Vector(5, 10, 15)", code)


# ============================================================
# Boolean Module Script Generation Tests
# ============================================================

class TestBooleanScriptGeneration(unittest.TestCase):
    """Tests that boolean module generates correct FreeCAD scripts."""

    @patch("freecad_cli.core.boolean.run_script")
    def test_fuse_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.boolean import fuse
        fuse("/tmp/test.FCStd", "Result", "Box1", "Box2")
        code = mock_run.call_args[0][0]
        self.assertIn("Part::Fuse", code)
        self.assertIn("'Box1'", code)
        self.assertIn("'Box2'", code)

    @patch("freecad_cli.core.boolean.run_script")
    def test_cut_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.boolean import cut
        cut("/tmp/test.FCStd", "Result", "Base", "Tool")
        code = mock_run.call_args[0][0]
        self.assertIn("Part::Cut", code)

    @patch("freecad_cli.core.boolean.run_script")
    def test_multi_fuse_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.boolean import multi_fuse
        multi_fuse("/tmp/test.FCStd", "Merged", ["A", "B", "C"])
        code = mock_run.call_args[0][0]
        self.assertIn("Part::MultiFuse", code)
        self.assertIn("['A', 'B', 'C']", code)


# ============================================================
# Export Module Tests
# ============================================================

class TestExportModule(unittest.TestCase):
    """Tests for export module."""

    def test_list_formats(self):
        from freecad_cli.core.export import list_formats
        result = list_formats()
        self.assertEqual(result["status"], "ok")
        names = [f["name"] for f in result["formats"]]
        self.assertIn("step", names)
        self.assertIn("stl", names)
        self.assertIn("iges", names)
        self.assertIn("brep", names)

    @patch("freecad_cli.core.export.run_script")
    def test_export_step_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.export import export_object
        export_object("/tmp/test.FCStd", "/tmp/out.step", object_names=["Box"])
        code = mock_run.call_args[0][0]
        self.assertIn("Part.export", code)
        self.assertIn("/tmp/out.step", code)

    @patch("freecad_cli.core.export.run_script")
    def test_export_stl_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.export import export_object
        export_object("/tmp/test.FCStd", "/tmp/out.stl")
        code = mock_run.call_args[0][0]
        self.assertIn("Mesh.export", code)


# ============================================================
# Transform Module Script Generation Tests
# ============================================================

class TestTransformScriptGeneration(unittest.TestCase):
    """Tests that transform module generates correct scripts."""

    @patch("freecad_cli.core.transform.run_script")
    def test_move_delta(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.transform import move
        move("/tmp/test.FCStd", "Box", dx=10, dy=20, dz=30)
        code = mock_run.call_args[0][0]
        self.assertIn("FreeCAD.Vector(10, 20, 30)", code)
        # Delta move uses addition
        self.assertIn("+", code)

    @patch("freecad_cli.core.transform.run_script")
    def test_move_absolute(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.transform import move
        move("/tmp/test.FCStd", "Box", dx=10, dy=20, dz=30, absolute=True)
        code = mock_run.call_args[0][0]
        self.assertIn("= FreeCAD.Vector(10, 20, 30)", code)

    @patch("freecad_cli.core.transform.run_script")
    def test_rotate_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.transform import rotate
        rotate("/tmp/test.FCStd", "Box", axis_z=1, angle=45)
        code = mock_run.call_args[0][0]
        self.assertIn("FreeCAD.Rotation", code)
        self.assertIn("45", code)


# ============================================================
# Measure Module Script Generation Tests
# ============================================================

class TestMeasureScriptGeneration(unittest.TestCase):
    """Tests that measure module generates correct scripts."""

    @patch("freecad_cli.core.measure.run_script")
    def test_measure_object_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.measure import measure_object
        measure_object("/tmp/test.FCStd", "Box")
        code = mock_run.call_args[0][0]
        self.assertIn("shape.Volume", code)
        self.assertIn("shape.Area", code)
        self.assertIn("CenterOfMass", code)
        self.assertIn("shape.Vertexes", code)

    @patch("freecad_cli.core.measure.run_script")
    def test_distance_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.measure import distance_between
        distance_between("/tmp/test.FCStd", "A", "B")
        code = mock_run.call_args[0][0]
        self.assertIn("distToShape", code)
        self.assertIn("'A'", code)
        self.assertIn("'B'", code)


# ============================================================
# Sketch Module Script Generation Tests
# ============================================================

class TestSketchScriptGeneration(unittest.TestCase):
    """Tests that sketch module generates correct scripts."""

    @patch("freecad_cli.core.sketch.run_script")
    def test_create_sketch_xy(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.sketch import create_sketch
        create_sketch("/tmp/test.FCStd", "MySketch", plane="XY")
        code = mock_run.call_args[0][0]
        self.assertIn("Sketcher::SketchObject", code)
        self.assertIn("Rotation(0,0,0,1)", code)  # XY plane

    @patch("freecad_cli.core.sketch.run_script")
    def test_create_sketch_xz(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.sketch import create_sketch
        create_sketch("/tmp/test.FCStd", "MySketch", plane="XZ")
        code = mock_run.call_args[0][0]
        self.assertIn("Vector(1,0,0)", code)  # XZ plane rotation axis

    @patch("freecad_cli.core.sketch.run_script")
    def test_add_line_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.sketch import add_line
        add_line("/tmp/test.FCStd", "Sketch", 0, 0, 10, 20)
        code = mock_run.call_args[0][0]
        self.assertIn("Part.LineSegment", code)
        self.assertIn("FreeCAD.Vector(0, 0, 0)", code)
        self.assertIn("FreeCAD.Vector(10, 20, 0)", code)

    @patch("freecad_cli.core.sketch.run_script")
    def test_add_rectangle_script(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        from freecad_cli.core.sketch import add_rectangle
        add_rectangle("/tmp/test.FCStd", "Sketch", 0, 0, 10, 20)
        code = mock_run.call_args[0][0]
        # Should have 4 lines
        self.assertEqual(code.count("Part.LineSegment"), 4)
        # Should have coincident constraints
        self.assertIn("Coincident", code)
        # Should have horizontal/vertical constraints
        self.assertIn("Horizontal", code)
        self.assertIn("Vertical", code)


# ============================================================
# CLI Structure Tests
# ============================================================

class TestCLIStructure(unittest.TestCase):
    """Tests that CLI commands are properly registered."""

    def test_cli_group_exists(self):
        from freecad_cli.freecad_cli import cli
        self.assertIsNotNone(cli)

    def test_cli_has_subcommands(self):
        from freecad_cli.freecad_cli import cli
        commands = cli.commands
        expected = ["session", "document", "object", "part", "sketch",
                    "partdesign", "boolean", "transform", "export",
                    "import", "measure", "repl"]
        for name in expected:
            self.assertIn(name, commands, f"Missing command group: {name}")

    def test_session_subcommands(self):
        from freecad_cli.freecad_cli import session
        self.assertIn("version", session.commands)
        self.assertIn("health", session.commands)
        self.assertIn("modules", session.commands)

    def test_document_subcommands(self):
        from freecad_cli.freecad_cli import document
        self.assertIn("new", document.commands)
        self.assertIn("info", document.commands)
        self.assertIn("save", document.commands)

    def test_part_subcommands(self):
        from freecad_cli.freecad_cli import part
        expected = ["box", "cylinder", "sphere", "cone", "torus"]
        for name in expected:
            self.assertIn(name, part.commands, f"Missing part command: {name}")

    def test_boolean_subcommands(self):
        from freecad_cli.freecad_cli import boolean
        expected = ["fuse", "cut", "common", "multi-fuse"]
        for name in expected:
            self.assertIn(name, boolean.commands, f"Missing boolean command: {name}")

    def test_repl_class(self):
        from freecad_cli.freecad_cli import FreeCADREPL
        repl = FreeCADREPL()
        self.assertTrue(hasattr(repl, "do_open"))
        self.assertTrue(hasattr(repl, "do_quit"))
        self.assertTrue(hasattr(repl, "do_objects"))
        self.assertTrue(hasattr(repl, "do_measure"))


if __name__ == "__main__":
    unittest.main()

"""End-to-end tests for FreeCAD CLI harness.

These tests execute actual CLI commands via subprocess and require
FreeCAD to be installed. Tests are skipped if FreeCAD is not available.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


def _resolve_cli(name):
    """Resolve CLI command path.

    If CLI_ANYTHING_FORCE_INSTALLED=1, use the installed command.
    Otherwise, fall back to python -m invocation.
    """
    if os.environ.get("CLI_ANYTHING_FORCE_INSTALLED") == "1":
        path = shutil.which(name)
        if path:
            return [path]
        raise RuntimeError(f"{name} not found in PATH")
    # Fall back to module invocation
    return [sys.executable, "-m", "freecad_cli.freecad_cli"]


def _freecad_available():
    """Check if FreeCADCmd is available."""
    try:
        from freecad_cli.utils.runner import find_freecad_cmd
        find_freecad_cmd()
        return True
    except Exception:
        return False


SKIP_REASON = "FreeCAD not available"


class TestCLISubprocess(unittest.TestCase):
    """Base class for subprocess-based CLI tests."""

    @classmethod
    def setUpClass(cls):
        cls.cli_cmd = _resolve_cli("freecad-cli")
        cls.tmpdir = tempfile.mkdtemp(prefix="freecad_cli_test_")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def run_cli(self, args, json_mode=True, timeout=120):
        """Run CLI command and return parsed result."""
        cmd = list(self.cli_cmd)
        if json_mode:
            cmd.append("--json")
        cmd.extend(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self.tmpdir,
        )
        if json_mode and result.stdout.strip():
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                return {"raw_stdout": result.stdout, "raw_stderr": result.stderr,
                        "returncode": result.returncode}
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }


class TestCLIVersion(TestCLISubprocess):
    """Test CLI version and help."""

    def test_version(self):
        result = subprocess.run(
            self.cli_cmd + ["--version"],
            capture_output=True, text=True,
        )
        self.assertIn("0.1.0", result.stdout)

    def test_help(self):
        result = subprocess.run(
            self.cli_cmd + ["--help"],
            capture_output=True, text=True,
        )
        self.assertIn("CLI harness for FreeCAD", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_export_formats(self):
        result = self.run_cli(["export", "formats"])
        self.assertEqual(result["status"], "ok")
        names = [f["name"] for f in result["formats"]]
        self.assertIn("step", names)
        self.assertIn("stl", names)


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestDocumentLifecycle(TestCLISubprocess):
    """Test document create -> info -> save workflow."""

    def test_create_document(self):
        filepath = os.path.join(self.tmpdir, "test_create.FCStd")
        result = self.run_cli(["document", "new", filepath])
        self.assertEqual(result["status"], "ok")
        self.assertTrue(os.path.exists(filepath))

    def test_document_info(self):
        filepath = os.path.join(self.tmpdir, "test_info.FCStd")
        self.run_cli(["document", "new", filepath])
        result = self.run_cli(["document", "info", filepath])
        self.assertEqual(result["status"], "ok")
        self.assertIn("document", result)

    def test_document_save_as(self):
        filepath = os.path.join(self.tmpdir, "test_saveas_src.FCStd")
        new_path = os.path.join(self.tmpdir, "test_saveas_dst.FCStd")
        self.run_cli(["document", "new", filepath])
        result = self.run_cli(["document", "save", filepath, "--as", new_path])
        self.assertEqual(result["status"], "ok")
        self.assertTrue(os.path.exists(new_path))


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestPrimitiveCreation(TestCLISubprocess):
    """Test creating primitive shapes."""

    def setUp(self):
        self.filepath = os.path.join(self.tmpdir, "test_prims.FCStd")
        self.run_cli(["document", "new", self.filepath])

    def test_add_box(self):
        result = self.run_cli([
            "part", "box", self.filepath, "TestBox",
            "-l", "10", "-w", "20", "-h", "30",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertAlmostEqual(result["object"]["volume"], 6000.0, places=1)

    def test_add_cylinder(self):
        result = self.run_cli([
            "part", "cylinder", self.filepath, "TestCyl",
            "-r", "5", "-h", "20",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["object"]["volume"], 0)

    def test_add_sphere(self):
        result = self.run_cli([
            "part", "sphere", self.filepath, "TestSphere",
            "-r", "10",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["object"]["volume"], 4000)  # 4/3 * pi * 10^3

    def test_list_objects(self):
        self.run_cli([
            "part", "box", self.filepath, "Box1",
            "-l", "10", "-w", "10", "-h", "10",
        ])
        self.run_cli([
            "part", "cylinder", self.filepath, "Cyl1",
            "-r", "5", "-h", "10",
        ])
        result = self.run_cli(["object", "list", self.filepath])
        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["count"], 2)


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestBooleanOperations(TestCLISubprocess):
    """Test boolean operations on shapes."""

    def setUp(self):
        self.filepath = os.path.join(self.tmpdir, "test_bool.FCStd")
        self.run_cli(["document", "new", self.filepath])
        self.run_cli([
            "part", "box", self.filepath, "Box1",
            "-l", "20", "-w", "20", "-h", "20",
        ])
        self.run_cli([
            "part", "box", self.filepath, "Box2",
            "-l", "20", "-w", "20", "-h", "20",
            "--x", "10", "--y", "10", "--z", "10",
        ])

    def test_fuse(self):
        result = self.run_cli([
            "boolean", "fuse", self.filepath, "Fused",
            "--base", "Box1", "--tool", "Box2",
        ])
        self.assertEqual(result["status"], "ok")
        # Volume should be less than 2 * 8000 (due to overlap)
        self.assertGreater(result["object"]["volume"], 8000)
        self.assertLess(result["object"]["volume"], 16000)

    def test_cut(self):
        result = self.run_cli([
            "boolean", "cut", self.filepath, "Cut",
            "--base", "Box1", "--tool", "Box2",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["object"]["volume"], 0)
        self.assertLess(result["object"]["volume"], 8000)

    def test_common(self):
        result = self.run_cli([
            "boolean", "common", self.filepath, "Common",
            "--base", "Box1", "--tool", "Box2",
        ])
        self.assertEqual(result["status"], "ok")
        # Intersection of two overlapping 20x20x20 boxes at 10,10,10 offset
        self.assertAlmostEqual(result["object"]["volume"], 1000.0, places=0)


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestExportPipeline(TestCLISubprocess):
    """Test exporting objects to various formats."""

    def setUp(self):
        self.filepath = os.path.join(self.tmpdir, "test_export.FCStd")
        self.run_cli(["document", "new", self.filepath])
        self.run_cli([
            "part", "box", self.filepath, "ExportBox",
            "-l", "10", "-w", "20", "-h", "30",
        ])

    def test_export_step(self):
        output = os.path.join(self.tmpdir, "output.step")
        result = self.run_cli([
            "export", "file", self.filepath, output,
            "--objects", "ExportBox",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertTrue(os.path.exists(output))
        self.assertGreater(os.path.getsize(output), 0)

    def test_export_stl(self):
        output = os.path.join(self.tmpdir, "output.stl")
        result = self.run_cli([
            "export", "file", self.filepath, output,
            "--objects", "ExportBox",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertTrue(os.path.exists(output))


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestMeasurements(TestCLISubprocess):
    """Test measurement operations."""

    def setUp(self):
        self.filepath = os.path.join(self.tmpdir, "test_measure.FCStd")
        self.run_cli(["document", "new", self.filepath])
        self.run_cli([
            "part", "box", self.filepath, "MeasureBox",
            "-l", "10", "-w", "20", "-h", "30",
        ])

    def test_measure_object(self):
        result = self.run_cli(["measure", "object", self.filepath, "MeasureBox"])
        self.assertEqual(result["status"], "ok")
        m = result["measurements"]
        self.assertAlmostEqual(m["volume"], 6000.0, places=1)
        self.assertAlmostEqual(m["dimensions"]["x"], 10.0, places=1)
        self.assertAlmostEqual(m["dimensions"]["y"], 20.0, places=1)
        self.assertAlmostEqual(m["dimensions"]["z"], 30.0, places=1)

    def test_measure_bounds(self):
        result = self.run_cli(["measure", "bounds", self.filepath])
        self.assertEqual(result["status"], "ok")
        self.assertIn("bounds", result)

    def test_measure_distance(self):
        # Add second box offset
        self.run_cli([
            "part", "box", self.filepath, "Box2",
            "-l", "5", "-w", "5", "-h", "5",
            "--x", "20",
        ])
        result = self.run_cli([
            "measure", "distance", self.filepath, "MeasureBox", "Box2",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertAlmostEqual(result["min_distance"], 10.0, places=1)


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestTransformOperations(TestCLISubprocess):
    """Test transform operations."""

    def setUp(self):
        self.filepath = os.path.join(self.tmpdir, "test_transform.FCStd")
        self.run_cli(["document", "new", self.filepath])
        self.run_cli([
            "part", "box", self.filepath, "TransBox",
            "-l", "10", "-w", "10", "-h", "10",
        ])

    def test_move(self):
        result = self.run_cli([
            "transform", "move", self.filepath, "TransBox",
            "--dx", "50", "--dy", "50", "--dz", "50",
        ])
        self.assertEqual(result["status"], "ok")
        pos = result["object"]["placement"]["position"]
        self.assertAlmostEqual(pos["x"], 50.0, places=1)
        self.assertAlmostEqual(pos["y"], 50.0, places=1)

    def test_rotate(self):
        result = self.run_cli([
            "transform", "rotate", self.filepath, "TransBox",
            "--angle", "45",
        ])
        self.assertEqual(result["status"], "ok")


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestObjectInspection(TestCLISubprocess):
    """Test object inspection commands."""

    def setUp(self):
        self.filepath = os.path.join(self.tmpdir, "test_inspect.FCStd")
        self.run_cli(["document", "new", self.filepath])
        self.run_cli([
            "part", "box", self.filepath, "InspectBox",
            "-l", "10", "-w", "20", "-h", "30",
        ])

    def test_inspect_object(self):
        result = self.run_cli(["object", "info", self.filepath, "InspectBox"])
        self.assertEqual(result["status"], "ok")
        obj = result["object"]
        self.assertEqual(obj["name"], "InspectBox")
        self.assertIn("properties", obj)
        self.assertIn("shape", obj)

    def test_list_edges(self):
        result = self.run_cli(["object", "edges", self.filepath, "InspectBox"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["edge_count"], 12)  # Box has 12 edges

    def test_list_faces(self):
        result = self.run_cli(["object", "faces", self.filepath, "InspectBox"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["face_count"], 6)  # Box has 6 faces

    def test_delete_object(self):
        result = self.run_cli(["object", "delete", self.filepath, "InspectBox"])
        self.assertEqual(result["status"], "ok")
        # Verify deleted
        list_result = self.run_cli(["object", "list", self.filepath])
        names = [o["name"] for o in list_result.get("objects", [])]
        self.assertNotIn("InspectBox", names)


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestSessionCommands(TestCLISubprocess):
    """Test session commands."""

    def test_version(self):
        result = self.run_cli(["session", "version"])
        self.assertEqual(result["status"], "ok")
        self.assertIn("version", result)

    def test_health(self):
        result = self.run_cli(["session", "health"])
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["healthy"])

    def test_modules(self):
        result = self.run_cli(["session", "modules"])
        self.assertEqual(result["status"], "ok")
        self.assertIsInstance(result["modules"], list)
        module_names = [m["name"] for m in result["modules"]]
        self.assertIn("Part", module_names)


@unittest.skipUnless(_freecad_available(), SKIP_REASON)
class TestFullWorkflow(TestCLISubprocess):
    """Test a complete workflow: create -> shape -> boolean -> measure -> export."""

    def test_bracket_workflow(self):
        """Simulate creating a simple bracket with a hole."""
        fp = os.path.join(self.tmpdir, "bracket.FCStd")

        # Create document
        result = self.run_cli(["document", "new", fp])
        self.assertEqual(result["status"], "ok")

        # Create main body
        result = self.run_cli([
            "part", "box", fp, "Body",
            "-l", "100", "-w", "50", "-h", "10",
        ])
        self.assertEqual(result["status"], "ok")

        # Create hole cylinder
        result = self.run_cli([
            "part", "cylinder", fp, "Hole",
            "-r", "5", "-h", "20",
            "--x", "25", "--y", "25", "--z", "-5",
        ])
        self.assertEqual(result["status"], "ok")

        # Cut hole from body
        result = self.run_cli([
            "boolean", "cut", fp, "BracketBody",
            "--base", "Body", "--tool", "Hole",
        ])
        self.assertEqual(result["status"], "ok")
        bracket_volume = result["object"]["volume"]
        self.assertGreater(bracket_volume, 0)
        # Volume should be less than full box (100*50*10 = 50000)
        self.assertLess(bracket_volume, 50000)

        # Measure
        result = self.run_cli(["measure", "object", fp, "BracketBody"])
        self.assertEqual(result["status"], "ok")

        # Export to STEP
        step_path = os.path.join(self.tmpdir, "bracket.step")
        result = self.run_cli([
            "export", "file", fp, step_path,
            "--objects", "BracketBody",
        ])
        self.assertEqual(result["status"], "ok")
        self.assertTrue(os.path.exists(step_path))
        self.assertGreater(os.path.getsize(step_path), 100)


if __name__ == "__main__":
    unittest.main()

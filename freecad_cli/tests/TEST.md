# FreeCAD CLI Harness - Test Plan

## Test Strategy

### Unit Tests (`test_core.py`)
Tests that verify module logic using mocked FreeCAD execution.
No actual FreeCAD installation required.

### E2E Tests (`test_full_e2e.py`)
Tests that run actual FreeCAD CLI commands via subprocess.
Requires FreeCAD installed and accessible.

---

## Unit Test Plan

### 1. JSON Output Module (`utils/json_output.py`)
- [x] `wrap_json` produces correct marker-wrapped output
- [x] `extract_json` extracts JSON from marked output
- [x] `extract_json` returns None for output without markers
- [x] `format_output` produces JSON in json_mode
- [x] `format_output` produces human-readable text in default mode
- [x] Error formatting

### 2. Runner Module (`utils/runner.py`)
- [x] `build_script` generates valid Python with JSON markers
- [x] `build_script` with result_expr appends output call
- [x] `build_script` wraps code in try/except
- [x] `find_freecad_cmd` with custom path
- [x] `find_freecad_cmd` raises FreeCADNotFoundError when not found

### 3. Project Module (`core/project.py`)
- [x] `new_document` generates correct FreeCAD script
- [x] `open_document` generates correct FreeCAD script
- [x] `document_info` generates correct FreeCAD script
- [x] `list_objects` with type filter

### 4. Primitives Module (`core/primitives.py`)
- [x] `add_box` generates script with correct parameters
- [x] `add_cylinder` generates script with correct parameters
- [x] `add_sphere` generates script with correct parameters
- [x] `add_cone` generates script with correct parameters

### 5. Boolean Module (`core/boolean.py`)
- [x] `fuse` generates correct script
- [x] `cut` generates correct script
- [x] `multi_fuse` handles list of shape names

### 6. Export Module (`core/export.py`)
- [x] `list_formats` returns supported formats
- [x] Export path resolution

### 7. Transform Module (`core/transform.py`)
- [x] `move` with delta vs absolute
- [x] `rotate` with axis and angle

### 8. Measure Module (`core/measure.py`)
- [x] Script generation for object measurement
- [x] Script generation for distance measurement

### 9. Sketch Module (`core/sketch.py`)
- [x] `create_sketch` with plane selection
- [x] `add_line` generates correct geometry
- [x] `add_rectangle` generates 4 lines + constraints

### 10. CLI Entry Point (`freecad_cli.py`)
- [x] CLI group structure (Click commands registered)
- [x] JSON mode flag propagation
- [x] REPL class instantiation

---

## E2E Test Plan

### Prerequisites
- FreeCAD installed with FreeCADCmd in PATH or FREECAD_CMD set
- Tests skip gracefully if FreeCAD not available

### Workflow Tests
1. **Basic document lifecycle**: create -> info -> save -> reopen
2. **Primitive creation**: create doc -> add box -> add cylinder -> list objects
3. **Boolean operations**: create shapes -> fuse -> measure result
4. **Export pipeline**: create shape -> export STEP -> verify file exists
5. **Sketch + PartDesign**: create sketch -> add rectangle -> pad -> measure
6. **Transform pipeline**: create box -> move -> rotate -> verify placement
7. **Measurement pipeline**: create shapes -> measure each -> measure distance

### Subprocess Tests
- All tests use `TestCLISubprocess` base class
- Uses `_resolve_cli("freecad-cli")` to find installed command
- Tests actual CLI invocation via subprocess

---

## Test Results

### Run Date: 2026-03-15

### Unit Tests (test_core.py) - 54/54 PASSED
```
freecad_cli/tests/test_core.py::TestJsonOutput::test_extract_json_no_markers PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_extract_json_partial_markers PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_extract_json_valid PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_format_output_dict_values PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_format_output_error PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_format_output_human_mode PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_format_output_json_mode PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_format_output_list_values PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_wrap_json_produces_markers PASSED
freecad_cli/tests/test_core.py::TestJsonOutput::test_wrap_then_extract_roundtrip PASSED
freecad_cli/tests/test_core.py::TestRunner::test_build_script_basic PASSED
freecad_cli/tests/test_core.py::TestRunner::test_build_script_error_handling PASSED
freecad_cli/tests/test_core.py::TestRunner::test_build_script_indentation PASSED
freecad_cli/tests/test_core.py::TestRunner::test_build_script_with_result_expr PASSED
freecad_cli/tests/test_core.py::TestRunner::test_find_freecad_cmd_custom_path_exists PASSED
freecad_cli/tests/test_core.py::TestRunner::test_find_freecad_cmd_custom_path_missing PASSED
freecad_cli/tests/test_core.py::TestRunner::test_find_freecad_cmd_not_found_anywhere PASSED
freecad_cli/tests/test_core.py::TestErrors::test_document_error PASSED
freecad_cli/tests/test_core.py::TestErrors::test_export_error PASSED
freecad_cli/tests/test_core.py::TestErrors::test_freecad_not_found_error PASSED
freecad_cli/tests/test_core.py::TestErrors::test_geometry_error PASSED
freecad_cli/tests/test_core.py::TestErrors::test_script_execution_error PASSED
freecad_cli/tests/test_core.py::TestProjectScriptGeneration::test_delete_object_script PASSED
freecad_cli/tests/test_core.py::TestProjectScriptGeneration::test_document_info_script PASSED
freecad_cli/tests/test_core.py::TestProjectScriptGeneration::test_list_objects_with_filter PASSED
freecad_cli/tests/test_core.py::TestProjectScriptGeneration::test_new_document_script PASSED
freecad_cli/tests/test_core.py::TestProjectScriptGeneration::test_open_document_script PASSED
freecad_cli/tests/test_core.py::TestPrimitivesScriptGeneration::test_add_box_script PASSED
freecad_cli/tests/test_core.py::TestPrimitivesScriptGeneration::test_add_box_with_position PASSED
freecad_cli/tests/test_core.py::TestPrimitivesScriptGeneration::test_add_cone_script PASSED
freecad_cli/tests/test_core.py::TestPrimitivesScriptGeneration::test_add_cylinder_script PASSED
freecad_cli/tests/test_core.py::TestPrimitivesScriptGeneration::test_add_sphere_script PASSED
freecad_cli/tests/test_core.py::TestBooleanScriptGeneration::test_cut_script PASSED
freecad_cli/tests/test_core.py::TestBooleanScriptGeneration::test_fuse_script PASSED
freecad_cli/tests/test_core.py::TestBooleanScriptGeneration::test_multi_fuse_script PASSED
freecad_cli/tests/test_core.py::TestExportModule::test_export_step_script PASSED
freecad_cli/tests/test_core.py::TestExportModule::test_export_stl_script PASSED
freecad_cli/tests/test_core.py::TestExportModule::test_list_formats PASSED
freecad_cli/tests/test_core.py::TestTransformScriptGeneration::test_move_absolute PASSED
freecad_cli/tests/test_core.py::TestTransformScriptGeneration::test_move_delta PASSED
freecad_cli/tests/test_core.py::TestTransformScriptGeneration::test_rotate_script PASSED
freecad_cli/tests/test_core.py::TestMeasureScriptGeneration::test_distance_script PASSED
freecad_cli/tests/test_core.py::TestMeasureScriptGeneration::test_measure_object_script PASSED
freecad_cli/tests/test_core.py::TestSketchScriptGeneration::test_add_line_script PASSED
freecad_cli/tests/test_core.py::TestSketchScriptGeneration::test_add_rectangle_script PASSED
freecad_cli/tests/test_core.py::TestSketchScriptGeneration::test_create_sketch_xy PASSED
freecad_cli/tests/test_core.py::TestSketchScriptGeneration::test_create_sketch_xz PASSED
freecad_cli/tests/test_core.py::TestCLIStructure::test_boolean_subcommands PASSED
freecad_cli/tests/test_core.py::TestCLIStructure::test_cli_group_exists PASSED
freecad_cli/tests/test_core.py::TestCLIStructure::test_cli_has_subcommands PASSED
freecad_cli/tests/test_core.py::TestCLIStructure::test_document_subcommands PASSED
freecad_cli/tests/test_core.py::TestCLIStructure::test_part_subcommands PASSED
freecad_cli/tests/test_core.py::TestCLIStructure::test_repl_class PASSED
freecad_cli/tests/test_core.py::TestCLIStructure::test_session_subcommands PASSED
```

### E2E Tests (test_full_e2e.py) - 28/28 PASSED
```
freecad_cli/tests/test_full_e2e.py::TestCLIVersion::test_export_formats PASSED
freecad_cli/tests/test_full_e2e.py::TestCLIVersion::test_help PASSED
freecad_cli/tests/test_full_e2e.py::TestCLIVersion::test_version PASSED
freecad_cli/tests/test_full_e2e.py::TestDocumentLifecycle::test_create_document PASSED
freecad_cli/tests/test_full_e2e.py::TestDocumentLifecycle::test_document_info PASSED
freecad_cli/tests/test_full_e2e.py::TestDocumentLifecycle::test_document_save_as PASSED
freecad_cli/tests/test_full_e2e.py::TestPrimitiveCreation::test_add_box PASSED
freecad_cli/tests/test_full_e2e.py::TestPrimitiveCreation::test_add_cylinder PASSED
freecad_cli/tests/test_full_e2e.py::TestPrimitiveCreation::test_add_sphere PASSED
freecad_cli/tests/test_full_e2e.py::TestPrimitiveCreation::test_list_objects PASSED
freecad_cli/tests/test_full_e2e.py::TestBooleanOperations::test_common PASSED
freecad_cli/tests/test_full_e2e.py::TestBooleanOperations::test_cut PASSED
freecad_cli/tests/test_full_e2e.py::TestBooleanOperations::test_fuse PASSED
freecad_cli/tests/test_full_e2e.py::TestExportPipeline::test_export_step PASSED
freecad_cli/tests/test_full_e2e.py::TestExportPipeline::test_export_stl PASSED
freecad_cli/tests/test_full_e2e.py::TestMeasurements::test_measure_bounds PASSED
freecad_cli/tests/test_full_e2e.py::TestMeasurements::test_measure_distance PASSED
freecad_cli/tests/test_full_e2e.py::TestMeasurements::test_measure_object PASSED
freecad_cli/tests/test_full_e2e.py::TestTransformOperations::test_move PASSED
freecad_cli/tests/test_full_e2e.py::TestTransformOperations::test_rotate PASSED
freecad_cli/tests/test_full_e2e.py::TestObjectInspection::test_delete_object PASSED
freecad_cli/tests/test_full_e2e.py::TestObjectInspection::test_inspect_object PASSED
freecad_cli/tests/test_full_e2e.py::TestObjectInspection::test_list_edges PASSED
freecad_cli/tests/test_full_e2e.py::TestObjectInspection::test_list_faces PASSED
freecad_cli/tests/test_full_e2e.py::TestSessionCommands::test_health PASSED
freecad_cli/tests/test_full_e2e.py::TestSessionCommands::test_modules PASSED
freecad_cli/tests/test_full_e2e.py::TestSessionCommands::test_version PASSED
freecad_cli/tests/test_full_e2e.py::TestFullWorkflow::test_bracket_workflow PASSED
```

### Summary
- **Unit tests**: 54/54 passed (100%)
- **E2E tests**: 28/28 passed (100%) with FreeCAD 1.0.2
- **Total**: 82 passed, 0 failed
- **Version**: 0.1.0

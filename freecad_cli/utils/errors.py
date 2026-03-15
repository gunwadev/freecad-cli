"""Error types for FreeCAD CLI harness."""


class FreeCADCLIError(Exception):
    """Base error for FreeCAD CLI operations."""


class FreeCADNotFoundError(FreeCADCLIError):
    """FreeCADCmd executable not found."""


class ScriptExecutionError(FreeCADCLIError):
    """Error executing a FreeCAD script."""

    def __init__(self, message, stderr="", returncode=None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


class DocumentError(FreeCADCLIError):
    """Error related to document operations."""


class ExportError(FreeCADCLIError):
    """Error during export operations."""


class GeometryError(FreeCADCLIError):
    """Error creating or modifying geometry."""

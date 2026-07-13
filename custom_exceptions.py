"""
Custom exceptions for the F1 Front Wing CFD project.
Used to enforce explicit error handling and avoid bare try-except blocks.
"""

class CFDProjectError(Exception):
    """Base exception class for all errors in the CFD project."""
    pass

class GeometryError(CFDProjectError):
    """Exception raised when geometry generation or watertight normal orientation fails."""
    pass

class SimulationError(CFDProjectError):
    """Exception raised when an OpenFOAM solver command or directory setup fails."""
    pass

class ForceParsingError(CFDProjectError):
    """Exception raised when parsing forces from OpenFOAM output files fails."""
    pass

class PostProcessingError(CFDProjectError):
    """Exception raised when PyVista loading, slicing, or plotting fails."""
    pass

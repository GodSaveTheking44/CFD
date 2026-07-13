"""
Configuration and constants for the F1 Front Wing CFD Project.
Contains geometry parameters, physical constants, simulation settings,
and OpenFOAM case parameters.
"""

import os
from typing import Dict, Any, List

# --- Path Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEOMETRY_DIR = os.path.join(BASE_DIR, "geometry")
COMMON_DIR = os.path.join(BASE_DIR, "common")

# --- Physical Constants ---
RHO_AIR: float = 1.225          # Air density (kg/m^3) at sea level
NU_AIR: float = 1.5e-5           # Kinematic viscosity of air (m^2/s)
U_INF: float = 30.0             # Freestream velocity (m/s)

# --- Geometry Settings ---
# Main Wing (NACA 4412 variant)
WING_CHORD: float = 0.25
WING_SPAN: float = 0.25
WING_MAX_CAMBER: float = 0.06
WING_CAMBER_POSITION: float = 0.4
WING_MAX_THICKNESS: float = 0.12
WING_NUM_POINTS: int = 40
WING_ANGLE_OF_ATTACK_DEG: float = 8.0
WING_GROUND_CLEARANCE: float = 0.03
WING_EXTRUSION_START_Y: float = -0.02
WING_EXTRUSION_END_Y: float = 0.25

# Endplates
ENDPLATE_X_MIN: float = -0.02
ENDPLATE_X_MAX: float = 0.28
ENDPLATE_Z_MIN: float = 0.01
ENDPLATE_Z_MAX: float = 0.18
ENDPLATE_THICKNESS: float = 0.005

# Outwash endplate alignment
ENDPLATE_OUTWASH_FRONT_Y: float = 0.25
ENDPLATE_OUTWASH_BACK_Y: float = 0.29

# Inwash endplate alignment
ENDPLATE_INWASH_FRONT_Y: float = 0.25
ENDPLATE_INWASH_BACK_Y: float = 0.21

# Front Wheel (Cylinder)
WHEEL_CENTER_X: float = 0.45
WHEEL_CENTER_Z: float = 0.15
WHEEL_RADIUS: float = 0.15
WHEEL_START_Y: float = 0.28
WHEEL_END_Y: float = 0.43
WHEEL_NUM_SEGMENTS: int = 40

# --- Force Coefficient Reference Values ---
COFR: List[float] = [0.125, 0.0, 0.05]  # Center of rotation for force coefficients
L_REF: float = 0.25                    # Reference length (wing chord)
A_REF: float = 0.0625                  # Reference area (wing chord * wing span)

# --- Simulation Settings ---
DESIGNS: List[str] = ["outwash", "inwash"]

# Mesh levels definition
MESH_LEVELS: Dict[str, Dict[str, int]] = {
    "coarse": {
        "NX": 36, "NY": 12, "NZ": 10,
        "SURF_REF_MIN": 2, "SURF_REF_MAX": 3,
        "WHEEL_REF_MIN": 1, "WHEEL_REF_MAX": 2,
        "WAKE_REF_LEVEL": 1, "FEAT_REF_LEVEL": 2
    },
    "medium": {
        "NX": 54, "NY": 18, "NZ": 15,
        "SURF_REF_MIN": 3, "SURF_REF_MAX": 4,
        "WHEEL_REF_MIN": 2, "WHEEL_REF_MAX": 3,
        "WAKE_REF_LEVEL": 2, "FEAT_REF_LEVEL": 3
    },
    "fine": {
        "NX": 72, "NY": 24, "NZ": 20,
        "SURF_REF_MIN": 4, "SURF_REF_MAX": 5,
        "WHEEL_REF_MIN": 3, "WHEEL_REF_MAX": 4,
        "WAKE_REF_LEVEL": 3, "FEAT_REF_LEVEL": 4
    }
}

# --- Post-Processing Slices ---
# Slices downstream behind wheel. Wheel trailing edge is at x = WHEEL_CENTER_X + WHEEL_RADIUS = 0.60m
# 0.5D, 1.0D, 2.0D stations:
SLICE_POSITIONS: List[float] = [0.75, 0.90, 1.20]
SLICE_NAMES: List[str] = ["0.5D", "1.0D", "2.0D"]

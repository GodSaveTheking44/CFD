"""
Unit tests for the F1 Front Wing CFD Project.
Tests geometry coordinate calculations, normal orientation checks, and force parsing.
"""

import os
import tempfile
import unittest
import numpy as np
import generate_geometry
import run_project
from custom_exceptions import GeometryError, ForceParsingError

class TestGeometryGenerator(unittest.TestCase):
    """Test suite for geometry generation module (generate_geometry.py)."""

    def test_naca_generation_valid(self) -> None:
        """Verifies that valid NACA parameters yield correct coordinate arrays."""
        num_points = 30
        chord = 0.25
        xu, zu, xl, zl = generate_geometry.generate_naca4(
            max_camber=0.06,
            camber_position=0.4,
            max_thickness=0.12,
            chord=chord,
            num_points=num_points
        )
        
        # Verify types and shapes
        self.assertIsInstance(xu, np.ndarray)
        self.assertIsInstance(zu, np.ndarray)
        self.assertEqual(len(xu), num_points)
        self.assertEqual(len(zu), num_points)
        
        # Leading edge should be at x=0
        self.assertAlmostEqual(xu[0], 0.0)
        self.assertAlmostEqual(xl[0], 0.0)
        
        # Trailing edge should be close to x=chord
        self.assertAlmostEqual(xu[-1], chord, places=3)
        self.assertAlmostEqual(xl[-1], chord, places=3)
        
        # Inverted camber check (z coordinates should represent inverted wing)
        # For cambered NACA 4412 inverted, suction surface points downwards, leading to negative z values
        self.assertTrue(np.all(zu <= 0.05))

    def test_naca_generation_invalid_camber_pos(self) -> None:
        """Verifies that out-of-bounds camber position raises GeometryError."""
        with self.assertRaises(GeometryError):
            generate_geometry.generate_naca4(
                max_camber=0.06,
                camber_position=1.5,  # Out of range [0, 1]
                max_thickness=0.12,
                chord=0.25,
                num_points=20
            )

    def test_naca_generation_invalid_chord(self) -> None:
        """Verifies that negative chord length raises GeometryError."""
        with self.assertRaises(GeometryError):
            generate_geometry.generate_naca4(
                max_camber=0.06,
                camber_position=0.4,
                max_thickness=0.12,
                chord=-0.1,  # Invalid negative chord
                num_points=20
            )

    def test_write_stl_invalid_shape(self) -> None:
        """Verifies that write_stl checks for wrong array shape."""
        bad_triangles = np.zeros((5, 3, 2))  # Wrong dimension (should be (K, 3, 3))
        with self.assertRaises(GeometryError):
            generate_geometry.write_stl("test_geom.stl", bad_triangles)

class TestForceParser(unittest.TestCase):
    """Test suite for force parsing routines in run_project.py."""

    def setUp(self) -> None:
        # Create a temporary directory for file output tests
        self.test_dir = tempfile.TemporaryDirectory()
        
        # Format typical OpenFOAM forceCoeffs.dat file structure
        self.valid_data = (
            "# Force coefficients header\n"
            "# Time  Cm  Cd  Cl  Cl(f)  Cl(r)\n"
            "0       0.05  0.80  -0.55  -0.27  -0.28\n"
            "10      0.04  0.75  -0.58  -0.29  -0.29\n"
            "20      0.03  0.72  -0.59  -0.30  -0.29\n"
        )
        self.corrupted_data = (
            "# Force coefficients header\n"
            "0   0.05   0.80\n"  # Missing columns
        )

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_parse_forces_valid(self) -> None:
        """Tests that valid force files are correctly parsed for Cd and Cl."""
        # Create folder structure: postProcessing/forceCoeffs1/0/
        dest_folder = os.path.join(self.test_dir.name, "postProcessing", "forceCoeffs1", "0")
        os.makedirs(dest_folder, exist_ok=True)
        
        file_path = os.path.join(dest_folder, "forceCoeffs.dat")
        with open(file_path, "w") as file_handle:
            file_handle.write(self.valid_data)
            
        cd, cl = run_project.parse_force_coefficients(self.test_dir.name)
        
        self.assertEqual(cd, 0.72)
        self.assertEqual(cl, -0.59)

    def test_parse_forces_missing_file(self) -> None:
        """Tests that missing files raise ForceParsingError."""
        with self.assertRaises(ForceParsingError):
            run_project.parse_force_coefficients(self.test_dir.name)

    def test_parse_forces_corrupted(self) -> None:
        """Tests that corrupted rows raise ForceParsingError."""
        dest_folder = os.path.join(self.test_dir.name, "postProcessing", "forceCoeffs1", "0")
        os.makedirs(dest_folder, exist_ok=True)
        
        file_path = os.path.join(dest_folder, "forceCoeffs.dat")
        with open(file_path, "w") as file_handle:
            file_handle.write(self.corrupted_data)
            
        with self.assertRaises(ForceParsingError):
            run_project.parse_force_coefficients(self.test_dir.name)

if __name__ == "__main__":
    unittest.main()

"""
Geometry generator for the F1 Front Wing CFD Project.
Generates watertight, oriented ASCII STL files for the wing,
wheel, and endplates using parameters from config.py.
"""

import os
import numpy as np
from typing import Tuple, List, Union
import config
from custom_exceptions import GeometryError

def write_stl(filename: str, triangles: np.ndarray, name: str = "mesh") -> None:
    """
    Writes a list of triangles to an ASCII STL file.

    Args:
        filename: Absolute path to the output STL file.
        triangles: Numpy array of shape (K, 3, 3) representing K triangles.
        name: Name of the solid body in the STL file.

    Raises:
        GeometryError: If validation of triangles fails or file write fails.
    """
    # Validation checks
    if not isinstance(triangles, np.ndarray):
        raise GeometryError("Triangles must be a numpy array.")
    if len(triangles.shape) != 3 or triangles.shape[1] != 3 or triangles.shape[2] != 3:
        raise GeometryError(
            f"Triangles array must have shape (K, 3, 3). Received shape: {triangles.shape}"
        )
    if triangles.shape[0] == 0:
        raise GeometryError("Triangles array cannot be empty.")

    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as file_handle:
            file_handle.write(f"solid {name}\n")
            for triangle in triangles:
                v0, v1, v2 = triangle
                edge_1 = v1 - v0
                edge_2 = v2 - v0
                normal = np.cross(edge_1, edge_2)
                norm_val = np.linalg.norm(normal)
                
                if norm_val > 1e-12:
                    normal /= norm_val
                else:
                    normal = np.array([0.0, 0.0, 0.0])
                    
                file_handle.write(
                    f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n"
                )
                file_handle.write("    outer loop\n")
                file_handle.write(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}\n")
                file_handle.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
                file_handle.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
                file_handle.write("    endloop\n")
                file_handle.write("  endfacet\n")
            file_handle.write(f"endsolid {name}\n")
    except OSError as err:
        raise GeometryError(f"Failed to write STL file to '{filename}': {err}")

def generate_naca4(
    max_camber: float,
    camber_position: float,
    max_thickness: float,
    chord: float,
    num_points: int = 40
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates a NACA 4-digit airfoil profile coordinates.

    Args:
        max_camber: Maximum camber value (e.g. 0.06 for 6%).
        camber_position: Location of max camber in tenths of chord (e.g. 0.4).
        max_thickness: Maximum thickness value (e.g. 0.12 for 12%).
        chord: Chord length of the airfoil in meters.
        num_points: Number of points to sample along the chord.

    Returns:
        Tuple containing (x_upper, z_upper, x_lower, z_lower) coordinate arrays.

    Raises:
        GeometryError: If input values are out of physical bounds.
    """
    if chord <= 0.0:
        raise GeometryError(f"Chord must be positive. Received: {chord}")
    if num_points < 3:
        raise GeometryError(f"Number of profile points must be >= 3. Received: {num_points}")
    if not (0.0 <= camber_position <= 1.0):
        raise GeometryError(f"Camber position must be in [0, 1]. Received: {camber_position}")

    x_coords = np.linspace(0.0, 1.0, num_points)
    mean_camber_line = np.zeros_like(x_coords)
    camber_gradient = np.zeros_like(x_coords)
    
    # Avoid divide by zero if camber position is exactly at 0 or 1
    p_val = max(1e-5, min(1.0 - 1e-5, camber_position))
    
    for i in range(len(x_coords)):
        xi = x_coords[i]
        if xi < p_val:
            mean_camber_line[i] = (max_camber / (p_val**2)) * (2.0 * p_val * xi - xi**2)
            camber_gradient[i] = (2.0 * max_camber / (p_val**2)) * (p_val - xi)
        else:
            mean_camber_line[i] = (max_camber / ((1.0 - p_val)**2)) * (
                (1.0 - 2.0 * p_val) + 2.0 * p_val * xi - xi**2
            )
            camber_gradient[i] = (2.0 * max_camber / ((1.0 - p_val)**2)) * (p_val - xi)
            
    half_thickness = 5.0 * max_thickness * (
        0.2969 * np.sqrt(x_coords) -
        0.1260 * x_coords -
        0.3516 * x_coords**2 +
        0.2843 * x_coords**3 -
        0.1015 * x_coords**4
    )
    theta = np.arctan(camber_gradient)
    
    x_upper = x_coords - half_thickness * np.sin(theta)
    z_upper = mean_camber_line + half_thickness * np.cos(theta)
    
    x_lower = x_coords + half_thickness * np.sin(theta)
    z_lower = mean_camber_line - half_thickness * np.cos(theta)
    
    # Scale by chord length
    x_upper *= chord
    z_upper *= chord
    x_lower *= chord
    z_lower *= chord
    
    # Invert for downforce (F1 wings have suction side facing down, camber facing down)
    z_upper = -z_upper
    z_lower = -z_lower
    
    return x_upper, z_upper, x_lower, z_lower

def create_wing_stl(filename: str) -> None:
    """
    Generates the main wing profile extruded in the spanwise (y) direction.

    Args:
        filename: Destination path for the wing STL.
    """
    x_upper, z_upper, x_lower, z_lower = generate_naca4(
        max_camber=config.WING_MAX_CAMBER,
        camber_position=config.WING_CAMBER_POSITION,
        max_thickness=config.WING_MAX_THICKNESS,
        chord=config.WING_CHORD,
        num_points=config.WING_NUM_POINTS
    )
    
    # Create closed profile: upper (LE->TE) then lower (TE->LE)
    # Concatenate upper and lower arrays while avoiding duplicates at leading/trailing edges
    x_profile = np.concatenate([x_upper, x_lower[::-1][1:-1]])
    z_profile = np.concatenate([z_upper, z_lower[::-1][1:-1]])
    
    num_profile_pts = len(x_profile)
    profile_2d = np.column_stack([x_profile, z_profile])
    
    # Rotate by angle of attack nose-down (clockwise rotation in XZ plane)
    angle_of_attack = np.radians(config.WING_ANGLE_OF_ATTACK_DEG)
    cos_a, sin_a = np.cos(angle_of_attack), np.sin(angle_of_attack)
    rotated_x = profile_2d[:, 0] * cos_a - profile_2d[:, 1] * sin_a
    rotated_z = profile_2d[:, 0] * sin_a + profile_2d[:, 1] * cos_a
    
    # Adjust ground clearance (lowest point at ground clearance height)
    min_z = np.min(rotated_z)
    rotated_z = rotated_z - min_z + config.WING_GROUND_CLEARANCE
    
    # Extrude in spanwise y direction
    y_start = config.WING_EXTRUSION_START_Y
    y_end = config.WING_EXTRUSION_END_Y
    
    vertices: List[List[float]] = []
    # Left cap vertices (y_start)
    for i in range(num_profile_pts):
        vertices.append([rotated_x[i], y_start, rotated_z[i]])
    # Right cap vertices (y_end)
    for i in range(num_profile_pts):
        vertices.append([rotated_x[i], y_end, rotated_z[i]])
        
    vertices_arr = np.array(vertices)
    
    # Centerline coordinates for normal orientation reference
    centerline_x = np.mean(rotated_x)
    centerline_z = np.mean(rotated_z)
    
    triangles: List[List[np.ndarray]] = []
    
    # 1. Left cap (y_start) - normal points in -y direction
    centroid_start = np.array([centerline_x, y_start, centerline_z])
    for i in range(num_profile_pts):
        next_i = (i + 1) % num_profile_pts
        triangles.append([centroid_start, vertices_arr[i], vertices_arr[next_i]])
        
    # 2. Right cap (y_end) - normal points in +y direction
    centroid_end = np.array([centerline_x, y_end, centerline_z])
    for i in range(num_profile_pts):
        next_i = (i + 1) % num_profile_pts
        triangles.append([centroid_end, vertices_arr[num_profile_pts + next_i], vertices_arr[num_profile_pts + i]])
        
    # 3. Mantle (connecting the two caps)
    for i in range(num_profile_pts):
        next_i = (i + 1) % num_profile_pts
        v0 = vertices_arr[i]
        v1 = vertices_arr[next_i]
        v2 = vertices_arr[num_profile_pts + i]
        v3 = vertices_arr[num_profile_pts + next_i]
        triangles.append([v0, v1, v2])
        triangles.append([v1, v3, v2])
        
    triangles_arr = np.array(triangles)
    
    # Orient normals outward
    oriented_triangles: List[np.ndarray] = []
    for triangle in triangles_arr:
        v0, v1, v2 = triangle
        edge_1 = v1 - v0
        edge_2 = v2 - v0
        normal = np.cross(edge_1, edge_2)
        norm_val = np.linalg.norm(normal)
        if norm_val > 1e-12:
            normal /= norm_val
        centroid = np.mean(triangle, axis=0)
        
        # Check boundary caps
        if np.abs(centroid[1] - y_start) < 1e-6:
            # Left cap: normal must point in -y
            if normal[1] > 0:
                oriented_triangles.append([v0, v2, v1])
            else:
                oriented_triangles.append([v0, v1, v2])
        elif np.abs(centroid[1] - y_end) < 1e-6:
            # Right cap: normal must point in +y
            if normal[1] < 0:
                oriented_triangles.append([v0, v2, v1])
            else:
                oriented_triangles.append([v0, v1, v2])
        else:
            # Mantle: normal must point radially outward from centerline
            radial_vector = np.array([centroid[0] - centerline_x, 0.0, centroid[2] - centerline_z])
            if np.dot(normal, radial_vector) < 0:
                oriented_triangles.append([v0, v2, v1])
            else:
                oriented_triangles.append([v0, v1, v2])
                
    write_stl(filename, np.array(oriented_triangles), name="wing")

def create_endplate_stl(filename: str, y_front: float, y_back: float) -> None:
    """
    Generates a thin box representing the endplate.
    Angles the plate outwards (outwash) or inwards (inwash).

    Args:
        filename: Destination path for the endplate STL.
        y_front: Spanwise y position at the endplate front.
        y_back: Spanwise y position at the endplate back.
    """
    x_min = config.ENDPLATE_X_MIN
    x_max = config.ENDPLATE_X_MAX
    z_min = config.ENDPLATE_Z_MIN
    z_max = config.ENDPLATE_Z_MAX
    thickness = config.ENDPLATE_THICKNESS
    
    y_front_inner = y_front - thickness / 2.0
    y_front_outer = y_front + thickness / 2.0
    y_back_inner = y_back - thickness / 2.0
    y_back_outer = y_back + thickness / 2.0
    
    vertices = np.array([
        [x_min, y_front_inner, z_min],  # 0
        [x_max, y_back_inner, z_min],   # 1
        [x_max, y_back_inner, z_max],   # 2
        [x_min, y_front_inner, z_max],  # 3
        [x_min, y_front_outer, z_min],  # 4
        [x_max, y_back_outer, z_min],   # 5
        [x_max, y_back_outer, z_max],   # 6
        [x_min, y_front_outer, z_max],  # 7
    ])
    
    faces = [
        [0, 2, 1], [0, 3, 2],       # Inner face
        [4, 5, 6], [4, 6, 7],       # Outer face
        [0, 7, 3], [0, 4, 7],       # Front face
        [1, 2, 6], [1, 6, 5],       # Back face
        [0, 5, 1], [0, 4, 5],       # Bottom face
        [3, 2, 6], [3, 6, 7],       # Top face
    ]
    
    triangles = []
    for face in faces:
        triangles.append([vertices[face[0]], vertices[face[1]], vertices[face[2]]])
        
    triangles_arr = np.array(triangles)
    box_center = np.mean(vertices, axis=0)
    
    oriented_triangles = []
    for triangle in triangles_arr:
        v0, v1, v2 = triangle
        edge_1 = v1 - v0
        edge_2 = v2 - v0
        normal = np.cross(edge_1, edge_2)
        norm_val = np.linalg.norm(normal)
        if norm_val > 1e-12:
            normal /= norm_val
        centroid = np.mean(triangle, axis=0)
        outward_vector = centroid - box_center
        if np.dot(normal, outward_vector) < 0:
            oriented_triangles.append([v0, v2, v1])
        else:
            oriented_triangles.append([v0, v1, v2])
            
    write_stl(filename, np.array(oriented_triangles), name="endplate")

def create_wheel_stl(filename: str) -> None:
    """
    Generates a cylinder representing the front wheel.

    Args:
        filename: Destination path for the wheel STL.
    """
    x_center = config.WHEEL_CENTER_X
    z_center = config.WHEEL_CENTER_Z
    radius = config.WHEEL_RADIUS
    y_start = config.WHEEL_START_Y
    y_end = config.WHEEL_END_Y
    num_segments = config.WHEEL_NUM_SEGMENTS
    
    theta = np.linspace(0.0, 2.0 * np.pi, num_segments, endpoint=False)
    x_circle = x_center + radius * np.cos(theta)
    z_circle = z_center + radius * np.sin(theta)
    
    vertices = []
    # Left cap vertices
    for i in range(num_segments):
        vertices.append([x_circle[i], y_start, z_circle[i]])
    # Right cap vertices
    for i in range(num_segments):
        vertices.append([x_circle[i], y_end, z_circle[i]])
        
    vertices_arr = np.array(vertices)
    
    triangles: List[List[np.ndarray]] = []
    
    # 1. Left cap (y_start) - normal points in -y direction
    centroid_start = np.array([x_center, y_start, z_center])
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        triangles.append([centroid_start, vertices_arr[i], vertices_arr[next_i]])
        
    # 2. Right cap (y_end) - normal points in +y direction
    centroid_end = np.array([x_center, y_end, z_center])
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        triangles.append([centroid_end, vertices_arr[num_segments + next_i], vertices_arr[num_segments + i]])
        
    # 3. Mantle
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        v0 = vertices_arr[i]
        v1 = vertices_arr[next_i]
        v2 = vertices_arr[num_segments + i]
        v3 = vertices_arr[num_segments + next_i]
        triangles.append([v0, v1, v2])
        triangles.append([v1, v3, v2])
        
    triangles_arr = np.array(triangles)
    
    oriented_triangles = []
    for triangle in triangles_arr:
        v0, v1, v2 = triangle
        edge_1 = v1 - v0
        edge_2 = v2 - v0
        normal = np.cross(edge_1, edge_2)
        norm_val = np.linalg.norm(normal)
        if norm_val > 1e-12:
            normal /= norm_val
        centroid = np.mean(triangle, axis=0)
        
        if np.abs(centroid[1] - y_start) < 1e-6:
            if normal[1] > 0:
                oriented_triangles.append([v0, v2, v1])
            else:
                oriented_triangles.append([v0, v1, v2])
        elif np.abs(centroid[1] - y_end) < 1e-6:
            if normal[1] < 0:
                oriented_triangles.append([v0, v2, v1])
            else:
                oriented_triangles.append([v0, v1, v2])
        else:
            radial_vector = np.array([centroid[0] - x_center, 0.0, centroid[2] - z_center])
            if np.dot(normal, radial_vector) < 0:
                oriented_triangles.append([v0, v2, v1])
            else:
                oriented_triangles.append([v0, v1, v2])
                
    write_stl(filename, np.array(oriented_triangles), name="wheel")

def main(output_dir: str = config.GEOMETRY_DIR) -> None:
    """
    Main function to execute geometry generation.
    Generates all components and saves them in the output directory.

    Args:
        output_dir: Directory where STL files will be written.
    """
    print(f"Generating geometries and writing to directory: '{output_dir}'...")
    os.makedirs(output_dir, exist_ok=True)
    
    wing_path = os.path.join(output_dir, "wing.stl")
    wheel_path = os.path.join(output_dir, "wheel.stl")
    outwash_path = os.path.join(output_dir, "endplate_outwash.stl")
    inwash_path = os.path.join(output_dir, "endplate_inwash.stl")
    
    create_wing_stl(wing_path)
    create_wheel_stl(wheel_path)
    create_endplate_stl(
        outwash_path,
        y_front=config.ENDPLATE_OUTWASH_FRONT_Y,
        y_back=config.ENDPLATE_OUTWASH_BACK_Y
    )
    create_endplate_stl(
        inwash_path,
        y_front=config.ENDPLATE_INWASH_FRONT_Y,
        y_back=config.ENDPLATE_INWASH_BACK_Y
    )
    print("Geometry generation completed successfully.")

if __name__ == "__main__":
    main()

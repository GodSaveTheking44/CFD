"""
Orchestration and driver script for the F1 Front Wing CFD Project.
Automates case setup, templates replacements, meshing (blockMesh, snappyHexMesh),
solver run (simpleFoam), and force coefficient parsing across designs and mesh levels.
"""

import os
import shutil
import subprocess
import glob
from typing import Tuple, Dict, Any, List, Optional
import config
import generate_geometry
from custom_exceptions import SimulationError, ForceParsingError

def execute_shell_command(command: str, working_dir: str, log_file_path: Optional[str] = None) -> None:
    """
    Executes a shell command inside a specified working directory,
    automatically sourcing the OpenFOAM environment if a bashrc is found.

    Args:
        command: The shell command string to run.
        working_dir: The directory in which to execute the command.
        log_file_path: Optional file path to redirect standard output and error.

    Raises:
        SimulationError: If the command returns a non-zero exit status.
    """
    print(f"[{working_dir}] Executing: {command}")
    
    # Locate OpenFOAM bashrc for sourcing (common in Docker/Linux installs)
    env_source_script = None
    search_paths = [
        "/usr/lib/openfoam/openfoam*/etc/bashrc",
        "/opt/openfoam*/etc/bashrc",
        "/usr/lib/openfoam/etc/bashrc"
    ]
    for path_pattern in search_paths:
        matches = glob.glob(path_pattern)
        if matches:
            env_source_script = matches[0]
            break
            
    if env_source_script:
        orchestrated_command = f"source {env_source_script} && {command}"
    else:
        orchestrated_command = command
        
    try:
        if log_file_path:
            log_dir = os.path.dirname(os.path.abspath(log_file_path))
            os.makedirs(log_dir, exist_ok=True)
            with open(log_file_path, "w") as log_file:
                process_result = subprocess.run(
                    ["/bin/bash", "-c", orchestrated_command],
                    cwd=working_dir,
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
        else:
            process_result = subprocess.run(
                ["/bin/bash", "-c", orchestrated_command],
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            if process_result.stdout:
                print(process_result.stdout)
                
        if process_result.returncode != 0:
            raise SimulationError(
                f"Command '{command}' failed in '{working_dir}' with exit status {process_result.returncode}."
            )
            
    except (OSError, subprocess.SubprocessError) as err:
        raise SimulationError(f"Failed to execute command '{command}' in '{working_dir}': {err}")

def parse_force_coefficients(case_directory: str) -> Tuple[float, float]:
    """
    Parses the final drag (Cd) and lift (Cl) coefficients from the forceCoeffs output file.

    Args:
        case_directory: Path to the OpenFOAM case folder.

    Returns:
        A tuple of (drag_coefficient, lift_coefficient).

    Raises:
        ForceParsingError: If files are missing, empty, or corrupted.
    """
    force_file_pattern = os.path.join(
        case_directory, "postProcessing", "forceCoeffs1", "*", "forceCoeffs.dat"
    )
    matching_files = glob.glob(force_file_pattern)
    
    if not matching_files:
        raise ForceParsingError(f"forceCoeffs.dat file not found in '{case_directory}'.")
        
    target_force_file = matching_files[0]
    
    try:
        with open(target_force_file, 'r') as file_handle:
            file_lines = file_handle.readlines()
            
        data_lines = [line for line in file_lines if not line.startswith('#') and line.strip()]
        if not data_lines:
            raise ForceParsingError(f"forceCoeffs.dat in '{case_directory}' contains no data rows.")
            
        # Parse the final iteration line (last line in the file)
        final_iteration_values = data_lines[-1].split()
        if len(final_iteration_values) < 4:
            raise ForceParsingError(
                f"Unexpected row format in force file. Line content: {final_iteration_values}"
            )
            
        drag_coefficient = float(final_iteration_values[2])
        lift_coefficient = float(final_iteration_values[3])
        return drag_coefficient, lift_coefficient
        
    except (IOError, ValueError, IndexError) as err:
        raise ForceParsingError(f"Failed to parse force coefficients from '{target_force_file}': {err}")

def _clean_directory(dir_path: str) -> None:
    """Removes a directory if it exists."""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def _copy_initial_conditions_and_constants(case_directory: str) -> None:
    """Copies initial conditions (0) and constants directories from common config."""
    shutil.copytree(os.path.join(config.COMMON_DIR, "0"), os.path.join(case_directory, "0"))
    shutil.copytree(os.path.join(config.COMMON_DIR, "constant"), os.path.join(case_directory, "constant"))

def _copy_system_config_files(case_directory: str) -> None:
    """Copies required system configuration dictionaries."""
    system_dest_dir = os.path.join(case_directory, "system")
    os.makedirs(system_dest_dir, exist_ok=True)
    required_system_files = ["controlDict", "fvSchemes", "fvSolution", "surfaceFeatureExtractDict"]
    for file_name in required_system_files:
        shutil.copy(
            os.path.join(config.COMMON_DIR, "system", file_name),
            os.path.join(system_dest_dir, file_name)
        )

def _copy_and_align_stl_files(case_directory: str, design: str) -> None:
    """Copies STL geometries to the case directory, aligning the correct endplate shape."""
    tri_surface_dir = os.path.join(case_directory, "constant", "triSurface")
    os.makedirs(tri_surface_dir, exist_ok=True)
    
    shutil.copy(
        os.path.join(config.GEOMETRY_DIR, "wing.stl"),
        os.path.join(tri_surface_dir, "wing.stl")
    )
    shutil.copy(
        os.path.join(config.GEOMETRY_DIR, "wheel.stl"),
        os.path.join(tri_surface_dir, "wheel.stl")
    )
    shutil.copy(
        os.path.join(config.GEOMETRY_DIR, f"endplate_{design}.stl"),
        os.path.join(tri_surface_dir, "endplate.stl")
    )

def _generate_block_mesh_dict(case_directory: str, mesh_params: Dict[str, int]) -> None:
    """Fills and writes the blockMeshDict dictionary using mesh parameters."""
    block_mesh_template_path = os.path.join(config.COMMON_DIR, "system", "blockMeshDict")
    with open(block_mesh_template_path, "r") as template_file:
        template_content = template_file.read()
        
    formatted_content = template_content.format(
        NX=mesh_params["NX"],
        NY=mesh_params["NY"],
        NZ=mesh_params["NZ"]
    )
    
    with open(os.path.join(case_directory, "system", "blockMeshDict"), "w") as target_file:
        target_file.write(formatted_content)

def _generate_snappy_hex_mesh_dict(case_directory: str, mesh_params: Dict[str, int]) -> None:
    """Fills and writes the snappyHexMeshDict dictionary using mesh parameters."""
    snappy_template_path = os.path.join(config.COMMON_DIR, "system", "snappyHexMeshDict")
    with open(snappy_template_path, "r") as template_file:
        template_content = template_file.read()
        
    formatted_content = template_content.format(
        SURF_REF_MIN=mesh_params["SURF_REF_MIN"],
        SURF_REF_MAX=mesh_params["SURF_REF_MAX"],
        WHEEL_REF_MIN=mesh_params["WHEEL_REF_MIN"],
        WHEEL_REF_MAX=mesh_params["WHEEL_REF_MAX"],
        WAKE_REF_LEVEL=mesh_params["WAKE_REF_LEVEL"],
        FEAT_REF_LEVEL=mesh_params["FEAT_REF_LEVEL"]
    )
    
    with open(os.path.join(case_directory, "system", "snappyHexMeshDict"), "w") as target_file:
        target_file.write(formatted_content)

def setup_case_directory(design: str, level: str, mesh_params: Dict[str, int]) -> str:
    """
    Sets up the directory structure and OpenFOAM dictionaries for a single case.

    Args:
        design: Wing design variant ("outwash" or "inwash").
        level: Mesh refinement level ("coarse", "medium", or "fine").
        mesh_params: Parameters dictionary for grid and refinement settings.

    Returns:
        The generated case folder name.
    """
    case_name = f"{design}_{level}"
    print(f"\n--- Setting up case directory: '{case_name}' ---")
    
    _clean_directory(case_name)
    os.makedirs(case_name, exist_ok=True)
    
    # Copy assets and configs
    _copy_initial_conditions_and_constants(case_name)
    _copy_system_config_files(case_name)
    _copy_and_align_stl_files(case_name, design)
    
    # Generate templates
    _generate_block_mesh_dict(case_name, mesh_params)
    _generate_snappy_hex_mesh_dict(case_name, mesh_params)
    
    return case_name

def execute_simulation_pipeline(case_name: str) -> None:
    """
    Runs feature extraction, background grid, snappy mesh, and RANS solver.

    Args:
        case_name: The case folder name to run the simulation inside.
    """
    print(f"\n=== Executing CFD Simulation Pipeline for '{case_name}' ===")
    
    # 1. Extract feature curves from STL surfaces
    execute_shell_command("surfaceFeatureExtract", case_name, log_file_path="log.surfaceFeatureExtract")
    
    # 2. Build structured background grid
    execute_shell_command("blockMesh", case_name, log_file_path="log.blockMesh")
    
    # 3. Refine and snap the volume mesh
    execute_shell_command("snappyHexMesh -overwrite", case_name, log_file_path="log.snappyHexMesh")
    
    # 4. Solve the RANS equations
    execute_shell_command("simpleFoam", case_name, log_file_path="log.simpleFoam")
    
    print(f"CFD Simulation Pipeline completed for '{case_name}'")

def main() -> None:
    """
    Main orchestration function.
    Generates geometry, runs simulations across designs/levels,
    and prints convergence tables.
    """
    # Step 1: Programmatically generate geometry STL files
    generate_geometry.main(config.GEOMETRY_DIR)
    
    study_results: List[Dict[str, Any]] = []
    
    # Step 2: Loop over design variants and refinement levels
    for design in config.DESIGNS:
        for level, mesh_params in config.MESH_LEVELS.items():
            case_folder = setup_case_directory(design, level, mesh_params)
            try:
                execute_simulation_pipeline(case_folder)
                drag_coeff, lift_coeff = parse_force_coefficients(case_folder)
                study_results.append({
                    "design": design,
                    "level": level,
                    "cd": drag_coeff,
                    "cl": lift_coeff,
                    "status": "Success"
                })
            except Exception as err:
                print(f"[ERROR] Failed case execution '{case_folder}': {err}")
                study_results.append({
                    "design": design,
                    "level": level,
                    "cd": None,
                    "cl": None,
                    "status": f"Failed: {err}"
                })
                
    # Step 3: Output formatted convergence results
    print("\n" + "=" * 65)
    print("                GRID INDEPENDENCE STUDY RESULTS")
    print("" + "=" * 65)
    print(f"{'Design':<12} | {'Mesh Level':<10} | {'Cd (Drag)':<10} | {'Cl (Lift)':<10} | {'Status':<10}")
    print("-" * 65)
    for row in study_results:
        cd_str = f"{row['cd']:.4f}" if row['cd'] is not None else "N/A"
        cl_str = f"{row['cl']:.4f}" if row['cl'] is not None else "N/A"
        print(f"{row['design'].capitalize():<12} | {row['level']:<10} | {cd_str:<10} | {cl_str:<10} | {row['status']:<10}")
    print("=" * 65 + "\n")
    
    # Step 4: Execute PyVista post-processing visualization
    print("Executing PyVista post-processing visualization dashboard...")
    try:
        subprocess.run(["python3", "post_process.py"], check=True)
    except subprocess.CalledProcessError as err:
        print(f"[ERROR] Post-processing dashboard compilation failed: {err}")

if __name__ == "__main__":
    main()

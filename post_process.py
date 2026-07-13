"""
Post-processing and visualization script for the F1 Front Wing CFD Project.
Extracts wake slices (velocity deficit and vorticity) and 3D streamlines,
rendering screenshots headlessly and combining them into a final comparative figure.
"""

import os
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from PIL import Image
from typing import Tuple, List
import config
from custom_exceptions import PostProcessingError

def process_case(case_dir: str, output_prefix: str) -> Tuple[List[str], str]:
    """
    Reads the OpenFOAM case, computes velocity deficit and vorticity magnitude,
    extracts 2D slices at downstream stations, seeds 3D streamlines, and saves PNGs.

    Args:
        case_dir: Folder path containing OpenFOAM output.
        output_prefix: Prefix string for generated image filenames.

    Returns:
        A tuple containing:
          - A list of generated slice image paths.
          - The generated top-view streamline image path.

    Raises:
        PostProcessingError: If loading, derivative calculation, or rendering fails.
    """
    print(f"Post-processing case: '{case_dir}'")
    
    # Create empty .foam file for PyVista reader
    foam_file_path = os.path.join(case_dir, "case.foam")
    try:
        with open(foam_file_path, 'w') as file_handle:
            pass
    except OSError as err:
        raise PostProcessingError(f"Failed to create dummy .foam file in '{case_dir}': {err}")
        
    # Load the OpenFOAM reader
    try:
        reader = pv.OpenFOAMReader(foam_file_path)
        if not reader.time_values:
            raise PostProcessingError(f"No time steps found in the OpenFOAM data for '{case_dir}'.")
        reader.set_active_time_value(reader.time_values[-1])
        multi_block_mesh = reader.read()
    except Exception as err:
        raise PostProcessingError(f"Failed to load OpenFOAM case '{case_dir}': {err}")
    
    # Extract internal mesh block
    internal_mesh = None
    if isinstance(multi_block_mesh, pv.MultiBlock):
        for block_key in multi_block_mesh.keys():
            if 'internal' in block_key.lower():
                internal_mesh = multi_block_mesh[block_key]
                break
        if internal_mesh is None:
            internal_mesh = multi_block_mesh[0]
    else:
        internal_mesh = multi_block_mesh
        
    if internal_mesh is None:
        raise PostProcessingError(f"Failed to extract internal mesh block from '{case_dir}'.")
        
    # Verify velocity array is present
    if 'U' not in internal_mesh.point_data:
        raise PostProcessingError(f"U velocity vector field not found in point data for '{case_dir}'.")
        
    # Calculate Velocity Deficit: 1.0 - Ux / Uinf
    try:
        velocity_vector = internal_mesh.point_data['U']
        velocity_x = velocity_vector[:, 0]
        velocity_deficit = 1.0 - (velocity_x / config.U_INF)
        internal_mesh.point_data['Velocity_Deficit'] = velocity_deficit
    except (IndexError, TypeError, ZeroDivisionError) as err:
        raise PostProcessingError(f"Failed to calculate velocity deficit for '{case_dir}': {err}")
    
    # Compute Vorticity vector and get its magnitude
    try:
        mesh_with_derivs = internal_mesh.compute_derivative(scalars='U', vorticity=True)
        vorticity_vector = mesh_with_derivs.point_data['vorticity']
        vorticity_magnitude = np.linalg.norm(vorticity_vector, axis=1)
        internal_mesh.point_data['Vorticity_Magnitude'] = vorticity_magnitude
    except Exception as err:
        raise PostProcessingError(f"Failed to compute vorticity field for '{case_dir}': {err}")
    
    # Check for underlying geometry STL files to overlay
    wing_stl_path = os.path.join(case_dir, "constant", "triSurface", "wing.stl")
    endplate_stl_path = os.path.join(case_dir, "constant", "triSurface", "endplate.stl")
    wheel_stl_path = os.path.join(case_dir, "constant", "triSurface", "wheel.stl")
    
    geometry_wing = pv.read(wing_stl_path) if os.path.exists(wing_stl_path) else None
    geometry_endplate = pv.read(endplate_stl_path) if os.path.exists(endplate_stl_path) else None
    geometry_wheel = pv.read(wheel_stl_path) if os.path.exists(wheel_stl_path) else None
    
    # ------------------ Slices (downstream stations) ------------------
    slice_files: List[str] = []
    
    for x_position, slice_name in zip(config.SLICE_POSITIONS, config.SLICE_NAMES):
        try:
            slice_mesh = internal_mesh.slice(normal='x', origin=(x_position, 0, 0))
            
            # 1. Plot and save Velocity Deficit
            plotter = pv.Plotter(off_screen=True, window_size=(800, 600))
            plotter.add_mesh(
                slice_mesh,
                scalars='Velocity_Deficit',
                cmap='coolwarm',
                clim=[0.0, 1.0],
                scalar_bar_args={'title': 'Velocity Deficit (1 - Ux/Uinf)'}
            )
            # Overlay wheel slice wireframe
            if geometry_wheel:
                wheel_slice = geometry_wheel.slice(normal='x', origin=(x_position, 0, 0))
                if wheel_slice.n_points > 0:
                    plotter.add_mesh(wheel_slice, color='black', line_width=4)
                    
            plotter.view_along_axis('x')
            plotter.camera.roll = 90
            plotter.camera.position = (x_position - 1.5, 0.25, 0.15)
            plotter.camera.focal_point = (x_position, 0.25, 0.15)
            plotter.camera.zoom(1.2)
            
            vel_filename = f"{output_prefix}_slice_vel_{slice_name}.png"
            plotter.screenshot(vel_filename)
            plotter.close()
            slice_files.append(vel_filename)
            
            # 2. Plot and save Vorticity Magnitude
            plotter = pv.Plotter(off_screen=True, window_size=(800, 600))
            plotter.add_mesh(
                slice_mesh,
                scalars='Vorticity_Magnitude',
                cmap='viridis',
                clim=[0.0, 500.0],
                scalar_bar_args={'title': 'Vorticity Magnitude (1/s)'}
            )
            if geometry_wheel:
                wheel_slice = geometry_wheel.slice(normal='x', origin=(x_position, 0, 0))
                if wheel_slice.n_points > 0:
                    plotter.add_mesh(wheel_slice, color='white', line_width=4)
                    
            plotter.view_along_axis('x')
            plotter.camera.roll = 90
            plotter.camera.position = (x_position - 1.5, 0.25, 0.15)
            plotter.camera.focal_point = (x_position, 0.25, 0.15)
            plotter.camera.zoom(1.2)
            
            vort_filename = f"{output_prefix}_slice_vort_{slice_name}.png"
            plotter.screenshot(vort_filename)
            plotter.close()
            
        except Exception as err:
            raise PostProcessingError(
                f"Failed to generate slices at station {slice_name} (x={x_position}m): {err}"
            )
        
    # ------------------ 3D Streamlines (Top View) ------------------
    try:
        # Seed line starts upstream of the wing, covering the wing span and wheel gap
        seed_line = pv.Line((-0.10, 0.02, 0.06), (-0.10, 0.38, 0.06), resolution=40)
        streamlines = internal_mesh.streamlines_from_source(
            seed_line,
            vectors='U',
            max_time=4.0,
            integration_direction='forward'
        )
        
        plotter = pv.Plotter(off_screen=True, window_size=(1200, 800))
        
        # Add transparent solid geometry overlays
        if geometry_wing:
            plotter.add_mesh(geometry_wing, color='lightgray', opacity=0.7, label='Wing')
        if geometry_endplate:
            plotter.add_mesh(geometry_endplate, color='red', opacity=0.8, label='Endplate')
        if geometry_wheel:
            plotter.add_mesh(geometry_wheel, color='dimgray', opacity=0.6, label='Wheel')
            
        # Draw streamlines colored by velocity deficit
        plotter.add_mesh(
            streamlines,
            scalars='Velocity_Deficit',
            cmap='coolwarm',
            clim=[0.0, 0.8],
            line_width=3,
            scalar_bar_args={'title': 'Velocity Deficit'}
        )
        
        # Top-down projection
        plotter.view_xy()
        plotter.camera.position = (0.6, 0.2, 1.8)
        plotter.camera.focal_point = (0.6, 0.2, 0.0)
        plotter.camera.up = (1, 0, 0)
        plotter.camera.zoom(1.1)
        
        streamline_file = f"{output_prefix}_streamlines_top.png"
        plotter.screenshot(streamline_file)
        plotter.close()
        
    except Exception as err:
        raise PostProcessingError(f"Failed to generate 3D streamlines: {err}")
        
    return slice_files, streamline_file

def generate_summary_figure(
    outwash_slices: List[str],
    outwash_streamlines: str,
    inwash_slices: List[str],
    inwash_streamlines: str
) -> None:
    """
    Combines outwash and inwash streamline and slice screenshots into a comparative grid.

    Args:
        outwash_slices: List of outwash slice image files.
        outwash_streamlines: Outwash streamline image file.
        inwash_slices: List of inwash slice image files.
        inwash_streamlines: Inwash streamline image file.
    """
    print("Combining figures into comparative summary dashboard...")
    summary_file = "wake_comparison_summary.png"
    
    try:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Row 1: Streamline comparison (Top View)
        img_out_stream = Image.open(outwash_streamlines)
        img_in_stream = Image.open(inwash_streamlines)
        
        axes[0, 0].imshow(img_out_stream)
        axes[0, 0].set_title("Outwash Wing (Pre-2026 Regulation) - Streamlines (Top View)", fontsize=14, fontweight='bold')
        axes[0, 0].axis('off')
        
        axes[0, 1].imshow(img_in_stream)
        axes[0, 1].set_title("Inwash Wing (2026 Regulation) - Streamlines (Top View)", fontsize=14, fontweight='bold')
        axes[0, 1].axis('off')
        
        # Row 2: Wake slice comparison at 1.0D station (x = 0.90m)
        img_out_slice = Image.open(outwash_slices[1])
        img_in_slice = Image.open(inwash_slices[1])
        
        axes[1, 0].imshow(img_out_slice)
        axes[1, 0].set_title("Outwash Wake Velocity Deficit at 1.0D behind Wheel", fontsize=14, fontweight='bold')
        axes[1, 0].axis('off')
        
        axes[1, 1].imshow(img_in_slice)
        axes[1, 1].set_title("Inwash Wake Velocity Deficit at 1.0D behind Wheel", fontsize=14, fontweight='bold')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(summary_file, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Summary comparative dashboard successfully saved to '{summary_file}'")
        
    except Exception as err:
        raise PostProcessingError(f"Failed to generate combined summary layout: {err}")

def main() -> None:
    """
    Main entry point for PyVista post-processing.
    Loads final/fine RANS cases and runs analysis.
    """
    outwash_dir = "outwash_fine"
    inwash_dir = "inwash_fine"
    
    # Fallback to defaults if fine directories are not found (e.g. running outside study)
    if not os.path.exists(outwash_dir) or not os.path.exists(inwash_dir):
        print("Warning: Fine mesh directories not found. Checking default names 'outwash' and 'inwash'...")
        outwash_dir = "outwash"
        inwash_dir = "inwash"
        
    if not os.path.exists(outwash_dir) or not os.path.exists(inwash_dir):
        print("Error: Simulation cases do not exist. Run simulations before post-processing.")
        return
        
    try:
        out_slices, out_stream = process_case(outwash_dir, "outwash")
        in_slices, in_stream = process_case(inwash_dir, "inwash")
        
        generate_summary_figure(out_slices, out_stream, in_slices, in_stream)
        print("Post-processing completed successfully.")
    except PostProcessingError as err:
        print(f"[ERROR] Post-processing failed: {err}")

if __name__ == "__main__":
    main()

# F1 Front Wing Wake Comparison: Outwash vs. Inwash Design
**CFD Study on Pre-2026 vs. 2026 Formula 1 Technical Regulations**

This project provides a fully automated, containerized 3D CFD pipeline to compare the aerodynamic wake characteristics of F1 front wings under two regulatory regimes: **Pre-2026 Outwash Wing Design** and **2026 Inwash Wing Design**.

---

## 1. Project Overview & Aerodynamic Context

F1's 2026 technical regulations overhaul the front wing geometry to solve a fundamental racing problem: "dirty air" wakes blocking overtaking.

*   **Pre-2026 "Outwash" Wing**: Directs airflow outward around the front wheels. While efficient for the leading car, it creates a wide, turbulent downstream wake that destabilizes following cars.
*   **2026 "Inwash" Wing**: Directs airflow inward, toward the car centerline. The goal is to draw the wheel wake into the low-pressure pocket behind the diffuser, throwing it high into the air and leaving a clean path for trailing cars.

This project quantifies the aerodynamic performance and wake profiles of these designs using **OpenFOAM (RANS steady-state solver)** and **PyVista (headless visualization)**.

---

## 2. Software Architecture & Separation of Concerns

The codebase is refactored into modular components, separating configuration, mathematics, execution, and rendering:

```
CFD/
├── config.py                # Single source of truth for physical, geometric, & grid settings
├── custom_exceptions.py     # Custom error classification (GeometryError, SimulationError, etc.)
├── generate_geometry.py     # Watertight ASCII STL generator (airfoil, endplates, wheel)
├── run_project.py           # Orchestrates directories, updates templates, and runs solvers
├── post_process.py          # PyVista headless visualization (slices, streamlines, plotting)
├── test_project.py          # Automated unit testing suite (airfoil math, normal vectors, parsing)
├── Dockerfile               # OpenFOAM v2406 base with system GL/EGL dependencies
├── requirements.txt         # Python package dependencies (numpy, pyvista, matplotlib, pillow)
├── run_pipeline.bat/.sh     # Multi-platform entry point scripts to build and run container
└── common/                  # OpenFOAM base template cases
    ├── 0/                   # Boundary conditions templates (U, p, k, omega, nut)
    ├── constant/            # Transport & turbulence model constants
    └── system/              # Solver schemes & mesh template files (snappyHexMeshDict, etc.)
```

---

## 3. Numerical Setup & CFD Methodology

*   **Solver**: Steady-state incompressible RANS using the `simpleFoam` solver.
*   **Turbulence Model**: $k$-$\omega$ SST (Shear Stress Transport) model, providing high accuracy for adverse pressure gradients and flow separation around the wheel.
*   **Grid Discretization**: Mesh generated via `blockMesh` and `snappyHexMesh` with a refinement box in the wheel wake and 3 inflation boundary layers.
*   **Boundary Conditions**:
    *   *Inlet*: Uniform velocity $U = 30\text{ m/s}$ (approx. $108\text{ km/h}$).
    *   *Outlet*: Zero static pressure ($p = 0$).
    *   *Ground*: Moving road wall boundary ($U_g = 30\text{ m/s}$) to eliminate artificial ground boundary layers.
    *   *Symmetry Plane*: Symmetry boundary at the center ($y = 0$).
    *   *Wing, Endplate, Wheel*: No-slip wall conditions.

---

## 4. Getting Started & Setup

### Prerequisites
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (must be running).

### Running the Complete Pipeline
The pipeline runs inside the Docker container and copies all results (case files, logs, and plots) back to your local host folder automatically.

*   **Windows**:
    ```cmd
    run_pipeline.bat
    ```
*   **Linux / macOS**:
    ```bash
    chmod +x run_pipeline.sh
    ./run_pipeline.sh
    ```

### Running the Unit Tests
You can run the unit tests locally (requires `numpy`):
```bash
python -m unittest test_project.py
```

---

## 5. Engineering Trade-offs & Assumptions

1.  **Stationary Wheel (v1)**: The wheel is modeled as a stationary cylinder. Real F1 tires rotate, creating top-wear vortices and separating the wake earlier. Future versions can implement **Multi-Reference Frame (MRF)** for wheel rotation.
2.  **Simplified Geometry**: High-fidelity F1 wings contain multiple elements (gurney flaps, slot gaps). A single cambered NACA profile was chosen here to optimize mesh size and solver convergence times.
3.  **Steady RANS**: Steady simulations approximate time-averaged wake profiles. Resolving transient vortex dynamics requires detached eddy simulations (DDES), which significantly increase computational cost.

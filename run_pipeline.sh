#!/bin/bash
set -e

echo "================================================================="
echo "       F1 FRONT WING CFD PIPELINE RUNNER (LINUX/MACOS)"
echo "================================================================="
echo

echo "Step 1: Building Docker image 'f1-wing-cfd' (includes OpenFOAM v2406 + Python + PyVista)..."
docker build -t f1-wing-cfd .

echo
echo "Step 2: Running the simulation pipeline inside the container..."
echo "(This will run Outwash vs. Inwash cases across Coarse, Medium, and Fine meshes)"
echo "(All plots, logs, and case folders will be written back to this directory)"
echo
docker run --rm -v "$(pwd):/project" f1-wing-cfd

echo
echo "================================================================="
echo "[SUCCESS] CFD Simulation and Post-processing complete!"
echo "Check this directory for:"
echo "  - case folders (e.g., outwash_fine/, inwash_fine/)"
echo "  - visualization plots (e.g., wake_comparison_summary.png)"
echo "  - report file (CFD_Report.md)"
echo "================================================================="

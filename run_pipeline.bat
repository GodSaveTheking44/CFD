@echo off
echo =================================================================
echo        F1 FRONT WING CFD PIPELINE RUNNER (WINDOWS)
echo =================================================================
echo.
echo Step 1: Building Docker image 'f1-wing-cfd' (includes OpenFOAM v2406 + Python + PyVista)...
docker build -t f1-wing-cfd .
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to build Docker image. Please make sure Docker Desktop is running.
    exit /b %errorlevel%
)

echo.
echo Step 2: Running the simulation pipeline inside the container...
echo (This will run Outwash vs. Inwash cases across Coarse, Medium, and Fine meshes)
echo (All plots, logs, and case folders will be written back to this directory)
echo.
docker run --rm -v "%cd%:/project" f1-wing-cfd

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Simulation pipeline failed. Check container logs.
    exit /b %errorlevel%
)

echo.
echo =================================================================
echo [SUCCESS] CFD Simulation and Post-processing complete!
echo Check this directory for:
echo   - case folders (e.g., outwash_fine/, inwash_fine/)
echo   - visualization plots (e.g., wake_comparison_summary.png)
echo   - report file (CFD_Report.md)
echo =================================================================

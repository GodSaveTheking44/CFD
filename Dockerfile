FROM opencfd/openfoam-default:2406

# Switch to root to install python and rendering dependencies
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    libgl1 \
    libegl1 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment to avoid system package conflicts
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install python packages required for running and post-processing
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pyvista pillow matplotlib numpy

# Set up project workspace
WORKDIR /project

# Copy project files and ensure correct ownership
COPY --chown=openfoam:openfoam . /project

# Switch back to openfoam user to run OpenFOAM cases safely
USER openfoam

# Run the automated pipeline by default
CMD ["python3", "run_project.py"]

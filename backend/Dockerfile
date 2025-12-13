FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# ✅ FIX 2: Install system build tools (Make Docker "Rich" like your Mac)
# - build-essential: provides gcc/make for compiling C extensions
# - libssl-dev: required for cryptography/python-jose
# - libffi-dev: required for cffi (used by cryptography)
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file
COPY environment_backend.yml /tmp/environment_backend.yml

# Create conda environment
RUN conda env create -f /tmp/environment_backend.yml && \
    conda clean -afy

# Activate conda for subsequent commands
SHELL ["bash", "-lc"]

# Set PATH
ENV CONDA_DEFAULT_ENV=credit-risk
ENV PATH=/opt/conda/envs/credit-risk/bin:$PATH

# Copy application code
COPY app /app/app

# Expose FastAPI port
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
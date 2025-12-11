# backend/Dockerfile

FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# Copy environment file
COPY environment_backend.yml /tmp/environment_backend.yml

# Create conda environment (ARM64 compatible)
RUN conda env create -f /tmp/environment_backend.yml && \
    conda clean -afy

# Activate conda for subsequent commands
SHELL ["bash", "-lc"]

# Set PATH for the created environment
ENV CONDA_DEFAULT_ENV=credit-risk
ENV PATH=/opt/conda/envs/credit-risk/bin:$PATH

# Copy application code
COPY app /app/app

# Expose FastAPI port
EXPOSE 8000

# Optional healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

# Start the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

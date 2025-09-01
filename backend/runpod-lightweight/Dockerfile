FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /workspace

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install only the most basic Python packages at build time
RUN pip install --no-cache-dir runpod

# Copy application files
COPY requirements.txt handler.py startup.sh ./

# Make startup script executable
RUN chmod +x startup.sh

# Set environment variables for model caching
ENV PYTHONPATH=/workspace
ENV HF_HOME=/workspace/models
ENV TORCH_CACHE=/workspace/models
ENV TRANSFORMERS_CACHE=/workspace/models

# Create models directory
RUN mkdir -p /workspace/models

# Use startup script that installs dependencies at runtime
CMD ["./startup.sh"]
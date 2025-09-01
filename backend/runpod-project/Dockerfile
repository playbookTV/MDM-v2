FROM --platform=linux/amd64 pytorch/pytorch:2.3.1-cuda12.1-cudnn8-devel

WORKDIR /workspace

# Install system dependencies including RunPod
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --timeout 900 runpod

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 3300 -r requirements.txt

# Copy handler code
COPY handler.py .

# Set environment variables for model caching
ENV PYTHONPATH=/workspace
ENV HF_HOME=/workspace/models
ENV TORCH_CACHE=/workspace/models
ENV TRANSFORMERS_CACHE=/workspace/models

# Create models directory
RUN mkdir -p /workspace/models

# Start the serverless handler
CMD ["python", "-u", "handler.py"]
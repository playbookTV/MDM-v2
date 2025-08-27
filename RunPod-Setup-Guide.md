# RunPod Setup Guide for Modomo AI Pipeline

## Overview

RunPod provides cloud GPU infrastructure perfect for running Modomo's AI processing pipeline with models like YOLO, SAM2, Depth Anything V2, and CLIP. This guide covers setup, deployment, and integration.

## RunPod Pricing & GPU Options (2025)

### Recommended GPUs for Modomo Pipeline

**For Development/Testing:**
- **RTX 4090 24GB**: $0.34/hr - Great for testing, sufficient VRAM for most models
- **RTX A6000 48GB**: ~$0.50/hr - High VRAM for large models

**For Production:**
- **A100 80GB**: $1.99/hr - Optimal performance for batch processing
- **H100 80GB**: $3.58/hr - Top performance for heavy workloads

### Cost Optimization
- **Spot Instances**: Up to 70% discount (not guaranteed availability)
- **On-Demand**: Guaranteed access, standard pricing
- **Serverless**: Pay per request, auto-scaling, millisecond billing

## Step 1: Account Setup

1. **Create Account**
   ```bash
   # Visit: https://console.runpod.io/signup
   ```

2. **Generate API Key**
   - Navigate to Settings → API Keys
   - Create new API key with appropriate permissions
   - Save the key securely (you'll need it for environment variables)

## Step 2: Install RunPod CLI

```bash
# Install runpodctl CLI
curl -sL https://runpod.io/install-runpodctl | bash

# Verify installation
runpodctl version

# Login with API key
runpodctl config --api-key YOUR_API_KEY
```

## Step 3: Deployment Options for Modomo

### Option A: GPU Pod with Custom Docker Image

**Create Dockerfile for Modomo AI Pipeline:**

```dockerfile
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY TUI/requirements.txt ./
COPY TUI/ai-requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r ai-requirements.txt

# Install AI model dependencies
RUN pip install ultralytics
RUN pip install git+https://github.com/openai/CLIP.git
RUN pip install git+https://github.com/badayvedat/Depth-Anything-V2.git@badayvedat-patch-1

# Copy application code
COPY TUI/src ./src

# Download model weights (optional - can be done at runtime)
RUN mkdir -p models

# Set Python path
ENV PYTHONPATH=/app/src

# Expose ports
EXPOSE 8000

# Default command
CMD ["python", "-m", "modomo_tui.main"]
```

**Deploy Pod:**

```bash
# Build and push Docker image
docker build -t your-registry/modomo-ai:latest .
docker push your-registry/modomo-ai:latest

# Create pod with custom image
runpodctl create pod \
    --name "modomo-ai-pipeline" \
    --image-name "your-registry/modomo-ai:latest" \
    --gpu-type "RTX4090" \
    --container-disk-in-gb 50 \
    --volume-in-gb 100 \
    --ports "8000:8000"
```

### Option B: Use Pre-built Template

```bash
# Use PyTorch template and install dependencies manually
runpodctl create pod \
    --name "modomo-ai" \
    --image-name "pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime" \
    --gpu-type "RTX4090" \
    --container-disk-in-gb 50 \
    --volume-in-gb 100
```

### Option C: Serverless Endpoint (Production)

**Create serverless handler:**

```python
# handler.py
import runpod
import torch
from modomo_tui.pipeline.processor import ImageProcessor

# Initialize processor globally
processor = ImageProcessor()

def process_image(event):
    """Process single image through Modomo AI pipeline"""
    try:
        image_url = event['input']['image_url']
        result = processor.process_image(image_url)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

runpod.serverless.start({
    "handler": process_image
})
```

**Deploy serverless:**

```bash
runpodctl project deploy \
    --name "modomo-serverless" \
    --cuda-version "11.8" \
    --python-version "3.10"
```

## Step 4: Environment Configuration

**Update your `.env` file:**

```bash
# RunPod Configuration
RUNPOD_API_KEY=your_runpod_api_key_here
RUNPOD_ENDPOINT_ID=your_endpoint_id  # For serverless
RUNPOD_POD_ID=your_pod_id           # For GPU pods

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST="8.0"  # For A100/H100

# Model Cache (use RunPod volume)
TRANSFORMERS_CACHE=/workspace/models
TORCH_HUB_CACHE=/workspace/models
```

## Step 5: Integration with Modomo TUI

**Update TUI configuration (`TUI/src/modomo_tui/models/config.py`):**

```python
class Config:
    # ... existing config ...
    
    # RunPod Integration
    RUNPOD_API_KEY: str = os.getenv("RUNPOD_API_KEY", "")
    RUNPOD_ENDPOINT_ID: str = os.getenv("RUNPOD_ENDPOINT_ID", "")
    USE_RUNPOD: bool = os.getenv("USE_RUNPOD", "false").lower() == "true"
    
    # GPU Configuration
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "4"))
```

**Create RunPod client (`TUI/src/modomo_tui/services/runpod_client.py`):**

```python
import requests
import os
from typing import Dict, Any

class RunPodClient:
    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY")
        self.endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}"
        
    def process_image(self, image_url: str) -> Dict[str, Any]:
        """Send image to RunPod serverless endpoint"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "image_url": image_url
            }
        }
        
        response = requests.post(
            f"{self.base_url}/runsync",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        return response.json()
```

## Step 6: Model Optimization for RunPod

**Memory Optimization:**

```python
# In your AI pipeline processor
import torch

# Enable memory optimization
torch.backends.cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True

# Use mixed precision
from torch.cuda.amp import autocast

@autocast()
def process_with_model(self, image):
    return self.model(image)
```

**Batch Processing:**

```python
# Process multiple images in batches
def process_batch(self, image_batch):
    with torch.no_grad():
        results = []
        for batch in torch.split(image_batch, self.batch_size):
            result = self.model(batch)
            results.append(result)
    return torch.cat(results)
```

## Step 7: Monitoring & Logging

**Add RunPod monitoring:**

```python
import logging
import time

class RunPodMonitor:
    def __init__(self):
        self.logger = logging.getLogger("runpod_monitor")
        
    def log_processing_time(self, start_time: float, image_count: int):
        duration = time.time() - start_time
        cost = self.calculate_cost(duration)
        
        self.logger.info(f"Processed {image_count} images in {duration:.2f}s")
        self.logger.info(f"Estimated cost: ${cost:.4f}")
        
    def calculate_cost(self, duration_seconds: float, gpu_type: str = "RTX4090"):
        hourly_rates = {
            "RTX4090": 0.34,
            "A100": 1.99,
            "H100": 3.58
        }
        rate = hourly_rates.get(gpu_type, 0.34)
        return (duration_seconds / 3600) * rate
```

## Step 8: Deployment Commands

**Quick Start Commands:**

```bash
# 1. Create pod for development
runpodctl create pod --name "modomo-dev" --image-name "pytorch/pytorch:latest" --gpu-type "RTX4090"

# 2. SSH into pod
runpodctl ssh modomo-dev

# 3. Install Modomo dependencies
pip install -r requirements.txt

# 4. Run TUI
PYTHONPATH=/workspace/src python -m modomo_tui.main

# 5. Stop pod when done
runpodctl stop modomo-dev
```

**Production Deployment:**

```bash
# Deploy serverless endpoint
runpodctl project deploy --name "modomo-production"

# Test endpoint
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"image_url": "https://example.com/image.jpg"}}'
```

## Cost Estimation

**Development (4 hours/day):**
- RTX 4090: $0.34 × 4 = $1.36/day
- Monthly: ~$41

**Production (24/7 with auto-scaling):**
- Serverless: Pay only for requests
- Estimated: $0.001-0.01 per image processed

## Best Practices

1. **Use Spot Instances** for non-critical workloads (70% cost savings)
2. **Implement Auto-scaling** with serverless for variable workloads
3. **Cache Models** on persistent volumes to avoid re-downloading
4. **Monitor Costs** with RunPod's built-in analytics
5. **Optimize Batch Sizes** based on GPU memory
6. **Use Mixed Precision** to fit larger models in memory

## Troubleshooting

**Common Issues:**

```bash
# Check GPU availability
nvidia-smi

# Check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"

# Monitor GPU memory
watch -n 1 nvidia-smi

# Check disk space
df -h

# View logs
runpodctl logs modomo-dev
```

This setup provides a scalable, cost-effective way to run your Modomo AI pipeline on RunPod's cloud GPUs with flexible pricing and auto-scaling capabilities.
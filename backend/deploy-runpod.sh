#!/bin/bash

# RunPod Deployment Script for Modomo AI Pipeline
# Usage: ./deploy-runpod.sh [pod-name] [gpu-type]

set -e

# Configuration
POD_NAME=${1:-"modomo-ai-pipeline"}
GPU_TYPE=${2:-"RTX4090"}
IMAGE_NAME="modomo-ai:latest"
REGISTRY="your-registry"  # Change this to your Docker registry

echo "🚀 Deploying Modomo AI Pipeline to RunPod..."
echo "Pod Name: $POD_NAME"
echo "GPU Type: $GPU_TYPE"
echo "Image: $REGISTRY/$IMAGE_NAME"

# Check if runpodctl is installed
if ! command -v runpodctl &> /dev/null; then
    echo "❌ runpodctl not found. Installing..."
    curl -sL https://runpod.io/install-runpodctl | bash
fi

# Check if logged in
if ! runpodctl config get api-key &> /dev/null; then
    echo "❌ Not logged in to RunPod. Please run:"
    echo "runpodctl config --api-key YOUR_API_KEY"
    exit 1
fi

echo "✅ RunPod CLI ready"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -f Dockerfile.runpod -t $REGISTRY/$IMAGE_NAME .

# Push to registry (if using remote registry)
if [ "$REGISTRY" != "local" ]; then
    echo "📤 Pushing image to registry..."
    docker push $REGISTRY/$IMAGE_NAME
fi

# Create RunPod
echo "🚀 Creating RunPod..."
runpodctl create pod \
    --name "$POD_NAME" \
    --image-name "$REGISTRY/$IMAGE_NAME" \
    --gpu-type "$GPU_TYPE" \
    --container-disk-in-gb 100 \
    --volume-in-gb 200 \
    --ports "8000:8000" \
    --env "CUDA_VISIBLE_DEVICES=0" \
    --env "TRANSFORMERS_CACHE=/workspace/models" \
    --env "TORCH_HUB_CACHE=/workspace/models"

echo "✅ RunPod created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. SSH into pod: runpodctl ssh $POD_NAME"
echo "2. Check GPU: nvidia-smi"
echo "3. Test health: curl http://localhost:8000/health"
echo "4. Monitor logs: runpodctl logs $POD_NAME"
echo ""
echo "💰 Estimated cost: $0.34/hour (RTX 4090)"
echo "🛑 Stop when done: runpodctl stop $POD_NAME"


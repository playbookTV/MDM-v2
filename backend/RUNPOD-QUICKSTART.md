# 🚀 RunPod Quick Start Guide for Modomo AI

Get your AI models running on RunPod in under 10 minutes!

## Prerequisites

1. **RunPod Account**: Sign up at [console.runpod.io](https://console.runpod.io)
2. **API Key**: Generate one in Settings → API Keys
3. **Docker**: Installed locally for building images

## Quick Deployment (3 Steps)

### Step 1: Install RunPod CLI
```bash
curl -sL https://runpod.io/install-runpodctl | bash
runpodctl config --api-key YOUR_API_KEY_HERE
```

### Step 2: Deploy AI Pipeline
```bash
# Make script executable
chmod +x deploy-runpod.sh

# Deploy with RTX 4090 (recommended for testing)
./deploy-runpod.sh "modomo-test" "RTX4090"

# Or deploy with A100 for production
./deploy-runpod.sh "modomo-prod" "A100"
```

### Step 3: Test Your Models
```bash
# SSH into your pod
runpodctl ssh modomo-test

# Check GPU
nvidia-smi

# Test health endpoint
curl http://localhost:8000/health

# Test AI pipeline (upload an image)
curl -X POST http://localhost:8000/api/v1/ai/process \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/test.jpg"}'
```

## What You Get

✅ **Complete AI Pipeline**:
- YOLOv8 for object detection
- SAM2 for segmentation masks  
- Depth Anything V2 for depth maps
- CLIP for scene classification
- Zero-shot furniture recognition

✅ **Production Ready**:
- Health checks and monitoring
- Error handling and logging
- GPU optimization
- Model caching

✅ **Cost Optimized**:
- RTX 4090: $0.34/hour (testing)
- A100: $1.99/hour (production)
- Auto-stop when idle

## Model Performance

| Model | Input Size | GPU Memory | Speed |
|-------|------------|------------|-------|
| YOLOv8n | 640x640 | 2GB | ~50ms |
| SAM2 | 1024x1024 | 4GB | ~200ms |
| Depth Anything | 518x518 | 3GB | ~150ms |
| CLIP | 224x224 | 1GB | ~20ms |

**Total Pipeline**: ~420ms per image on RTX 4090

## Environment Variables

```bash
# GPU Configuration
CUDA_VISIBLE_DEVICES=0
TRANSFORMERS_CACHE=/workspace/models
TORCH_HUB_CACHE=/workspace/models

# Model Paths
YOLO_MODEL_PATH=/app/models/yolov8n.pt
SAM_MODEL_PATH=/app/models/sam_vit_h_4b8939.pth
DEPTH_MODEL_PATH=/app/models/depth_anything_vitl14
```

## Troubleshooting

### Common Issues

**❌ CUDA Out of Memory**
```bash
# Reduce batch size or use smaller models
export BATCH_SIZE=1
export YOLO_MODEL=yolov8n.pt  # instead of yolov8l.pt
```

**❌ Model Download Failed**
```bash
# Check internet connection
curl -I https://huggingface.co

# Manual download
wget https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned.safetensors
```

**❌ Port Already in Use**
```bash
# Check what's using port 8000
netstat -tulpn | grep :8000

# Kill process or change port
export PORT=8001
```

### Performance Tips

1. **Use Spot Instances** for 70% cost savings
2. **Enable Model Caching** to avoid re-downloads
3. **Batch Processing** for multiple images
4. **Mixed Precision** for faster inference

## Next Steps

1. **Test with Real Images**: Upload some interior photos
2. **Monitor Performance**: Check GPU utilization and memory
3. **Scale Up**: Move to A100 for production workloads
4. **Serverless**: Deploy as serverless endpoint for auto-scaling

## Support

- **RunPod Docs**: [docs.runpod.io](https://docs.runpod.io)
- **Discord**: [discord.gg/runpod](https://discord.gg/runpod)
- **Issues**: Check the logs with `runpodctl logs pod-name`

---

**🎯 Ready to deploy? Run:**
```bash
./deploy-runpod.sh "my-modomo-ai" "RTX4090"
```


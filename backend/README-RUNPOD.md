# 🚀 Modomo AI Pipeline on RunPod

Complete AI pipeline deployment for interior design analysis using YOLO, SAM2, Depth Anything V2, and CLIP models.

## 🎯 What This Gives You

**Complete AI Pipeline:**
- 🎯 **Object Detection**: YOLOv8 for furniture identification
- ✂️ **Segmentation**: SAM2 for precise object masks
- 📏 **Depth Estimation**: Depth Anything V2 for 3D understanding
- 🏠 **Scene Classification**: CLIP for room type recognition
- 🪑 **Furniture Recognition**: Zero-shot classification with CLIP

**Production Features:**
- 🐳 Docker containerization
- 🚀 RunPod cloud GPU deployment
- 📊 Health monitoring and logging
- 💰 Cost optimization (RTX 4090: $0.34/hour)
- 🔄 Auto-scaling with serverless option

## 🚀 Quick Start (5 minutes)

### 1. Setup RunPod Account
```bash
# Sign up at console.runpod.io
# Generate API key in Settings → API Keys
```

### 2. Install RunPod CLI
```bash
curl -sL https://runpod.io/install-runpodctl | bash
runpodctl config --api-key YOUR_API_KEY
```

### 3. Deploy AI Pipeline
```bash
cd backend
chmod +x deploy-runpod.sh
./deploy-runpod.sh "modomo-ai" "RTX4090"
```

### 4. Test Your Models
```bash
# SSH into pod
runpodctl ssh modomo-ai

# Check GPU
nvidia-smi

# Test health
curl http://localhost:8000/health

# Test AI pipeline
python test-runpod.py
```

## 📁 File Structure

```
backend/
├── Dockerfile.runpod          # RunPod-optimized Docker image
├── deploy-runpod.sh          # One-click deployment script
├── runpod-handler.py         # Serverless handler for production
├── test-runpod.py            # Test suite for verification
├── ai-requirements.txt       # AI model dependencies
├── .env.runpod               # RunPod environment configuration
└── README-RUNPOD.md          # This file
```

## 🎮 Deployment Options

### Option A: GPU Pod (Development/Testing)
```bash
# RTX 4090 - Great for testing ($0.34/hour)
./deploy-runpod.sh "modomo-dev" "RTX4090"

# A100 - Production workloads ($1.99/hour)
./deploy-runpod.sh "modomo-prod" "A100"
```

### Option B: Serverless (Production)
```bash
# Deploy as serverless endpoint
runpodctl project deploy \
    --name "modomo-serverless" \
    --cuda-version "11.8" \
    --python-version "3.10"
```

## 🔧 Configuration

### Environment Variables
Copy `.env.runpod` to `.env` and update:
```bash
RUNPOD_API_KEY=your_actual_api_key
RUNPOD_ENDPOINT_ID=your_endpoint_id
```

### Model Selection
```bash
# Lightweight models (faster, less accurate)
export YOLO_MODEL=yolov8n.pt
export SAM_MODEL=sam_vit_b_01ec64.pth

# Heavy models (slower, more accurate)
export YOLO_MODEL=yolov8l.pt
export SAM_MODEL=sam_vit_h_4b8939.pth
```

## 📊 Performance Metrics

| Model | Input Size | GPU Memory | Speed (RTX 4090) |
|-------|------------|------------|-------------------|
| YOLOv8n | 640×640 | 2GB | ~50ms |
| SAM2 (ViT-H) | 1024×1024 | 4GB | ~200ms |
| Depth Anything | 518×518 | 3GB | ~150ms |
| CLIP (ViT-B/32) | 224×224 | 1GB | ~20ms |

**Total Pipeline**: ~420ms per image
**Throughput**: ~2.4 images/second

## 🧪 Testing

### Local Testing
```bash
# Test model availability
python test-runpod.py

# Test with custom image
curl -X POST http://localhost:8000/api/v1/ai/process \
  -H "Content-Type: application/json" \
  -d '{"image_url": "path/to/your/image.jpg"}'
```

### RunPod Testing
```bash
# SSH into pod
runpodctl ssh modomo-ai

# Run test suite
python test-runpod.py

# Check logs
runpodctl logs modomo-ai

# Monitor GPU
watch -n 1 nvidia-smi
```

## 🔍 Troubleshooting

### Common Issues

**❌ CUDA Out of Memory**
```bash
# Reduce batch size
export BATCH_SIZE=1

# Use smaller models
export YOLO_MODEL=yolov8n.pt
export SAM_MODEL=sam_vit_b_01ec64.pth
```

**❌ Model Download Failed**
```bash
# Check internet connection
curl -I https://huggingface.co

# Manual download
wget https://huggingface.co/facebook/sam-vit-huge/resolve/main/sam_vit_h_4b8939.pth
```

**❌ Port Already in Use**
```bash
# Check port usage
netstat -tulpn | grep :8000

# Change port
export PORT=8001
```

### Performance Optimization

1. **Enable Mixed Precision**
   ```bash
   export MIXED_PRECISION=true
   ```

2. **Optimize CUDA Settings**
   ```bash
   export TORCH_BACKENDS_CUDNN_BENCHMARK=true
   export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
   ```

3. **Use Spot Instances** (70% cost savings)
   ```bash
   runpodctl create pod --spot-instance true
   ```

## 💰 Cost Optimization

### Development (4 hours/day)
- RTX 4090: $0.34 × 4 = $1.36/day
- Monthly: ~$41

### Production (24/7)
- Serverless: Pay per request
- Estimated: $0.001-0.01 per image processed

### Cost Saving Tips
1. **Use Spot Instances** for non-critical workloads
2. **Auto-stop** pods when idle
3. **Batch Processing** multiple images
4. **Model Caching** to avoid re-downloads

## 🔄 Integration with Modomo

### API Endpoints
```bash
# Health check
GET /health

# Process single image
POST /api/v1/ai/process
{
  "image": "base64_encoded_image",
  "options": {
    "confidence_threshold": 0.25,
    "include_depth": true,
    "include_masks": true
  }
}

# Batch processing
POST /api/v1/ai/process-batch
{
  "images": ["base64_1", "base64_2"],
  "batch_size": 4
}
```

### Response Format
```json
{
  "status": "success",
  "result": {
    "scene_analysis": {
      "scene_type": "a living room",
      "confidence": 0.89
    },
    "objects": [
      {
        "bbox": [100, 150, 300, 400],
        "confidence": 0.92,
        "category": "sofa",
        "category_confidence": 0.87,
        "mask": [[0, 1, 1, 0], ...]
      }
    ],
    "depth_map": "base64_encoded_depth_map"
  }
}
```

## 🚀 Next Steps

1. **Deploy to RunPod**: Run `./deploy-runpod.sh`
2. **Test with Real Images**: Upload interior photos
3. **Monitor Performance**: Check GPU utilization
4. **Scale Up**: Move to A100 for production
5. **Serverless**: Deploy as auto-scaling endpoint

## 📚 Resources

- **RunPod Docs**: [docs.runpod.io](https://docs.runpod.io)
- **RunPod Discord**: [discord.gg/runpod](https://discord.gg/runpod)
- **Model Documentation**: [huggingface.co](https://huggingface.co)
- **PyTorch**: [pytorch.org](https://pytorch.org)

---

**🎯 Ready to deploy?**
```bash
cd backend
./deploy-runpod.sh "my-modomo-ai" "RTX4090"
```

**Questions?** Check the logs with `runpodctl logs pod-name` or join the RunPod Discord!


#!/bin/bash

# RunPod Quick Deploy Script
# Run this in your terminal to deploy the handler

echo "🚀 RunPod Handler Deployment"
echo "============================"
echo ""
echo "Since SSH isn't working, please follow these steps:"
echo ""
echo "1. Open Jupyter Lab in your browser:"
echo "   https://v92kcxqhcn8gst-8888.proxy.runpod.net/"
echo ""
echo "2. Click on 'Terminal' to open a new terminal"
echo ""
echo "3. Copy and paste these commands:"
echo ""
echo "cd /workspace"
echo ""
echo "# Download the handler directly"
echo "cat > handler.py << 'HANDLER_EOF'"
cat /Users/leslieisah/MDM/backend/handler_fixed.py
echo "HANDLER_EOF"
echo ""
echo "# Install dependencies"
echo "pip install runpod transformers torch torchvision ultralytics supervision groundingdino-py segment-anything-2 depth-anything-v2"
echo ""
echo "# Start the handler"
echo "python handler.py"
echo ""
echo "============================"
echo "After pasting, the handler will be deployed and running!"
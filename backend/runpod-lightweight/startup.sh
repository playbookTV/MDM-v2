#!/bin/bash
set -e

echo "🚀 Starting Modomo AI Pipeline deployment..."
echo "📦 Installing Python dependencies..."

# Install all AI dependencies at runtime
pip install --no-cache-dir -r requirements.txt

echo "✅ Dependencies installed successfully"
echo "🔄 Creating model cache directories..."

# Ensure model cache directories exist
mkdir -p /workspace/models
mkdir -p $HF_HOME
mkdir -p $TORCH_CACHE
mkdir -p $TRANSFORMERS_CACHE

echo "🎯 Starting AI handler..."
python -u handler.py
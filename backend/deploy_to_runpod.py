#!/usr/bin/env python3
"""Deploy handler to RunPod workspace"""

import os
import sys

# Create handler content
handler_content = open('/Users/leslieisah/MDM/backend/handler_fixed.py', 'r').read()

# Write to RunPod workspace
with open('/workspace/handler.py', 'w') as f:
    f.write(handler_content)

print("✅ Handler deployed to /workspace/handler.py")

# Install required packages
print("📦 Installing required packages...")
os.system("pip install runpod transformers torch torchvision ultralytics supervision groundingdino-py segment-anything-2 depth-anything-v2")

print("✅ Deployment complete!")
print("🚀 Your RunPod endpoint should now be ready at: https://v92kcxqhcn8gst-8888.proxy.runpod.net/")
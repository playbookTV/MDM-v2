"""
RunPod Deployment Instructions

1. Open Jupyter Lab at: https://v92kcxqhcn8gst-8888.proxy.runpod.net/
2. Open a terminal in Jupyter Lab
3. Run the following commands:

cd /workspace

# Download the handler
wget https://raw.githubusercontent.com/leslieis/MDM/main/backend/handler_fixed.py -O handler.py

# Or if wget doesn't work, use curl:
curl -o handler.py https://raw.githubusercontent.com/leslieis/MDM/main/backend/handler_fixed.py

# Install required packages
pip install runpod transformers torch torchvision ultralytics supervision groundingdino-py segment-anything-2 depth-anything-v2

# Test the handler
python -c "import handler; print('Handler loaded successfully!')"

4. The handler should now be deployed and ready to use!
"""

print(__doc__)
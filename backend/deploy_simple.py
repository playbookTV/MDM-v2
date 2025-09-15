import base64
import os

# Read the base64 encoded handler
with open('/tmp/handler_base64.txt', 'r') as f:
    encoded = f.read()

# Decode and write handler
handler_content = base64.b64decode(encoded).decode('utf-8')
with open('/workspace/handler.py', 'w') as f:
    f.write(handler_content)

print("Handler deployed to /workspace/handler.py")

# Test import
try:
    import runpod
    print("✅ RunPod SDK available")
except ImportError:
    print("Installing RunPod SDK...")
    os.system("pip install runpod")
    
print("Deployment complete!")
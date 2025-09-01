#!/usr/bin/env python3
"""
Deploy Modomo AI Pipeline to RunPod Pod via SSH
"""

import subprocess
import sys
import os

# RunPod connection details
RUNPOD_HOST = "i4mc5gqc7sepzc-644112d0@ssh.runpod.io"
SSH_KEY = "~/.ssh/id_ed25519"

def run_ssh_command(command):
    """Run command on RunPod pod via SSH"""
    ssh_cmd = f'ssh -i {SSH_KEY} {RUNPOD_HOST} "{command}"'
    print(f"Running: {command}")
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def copy_file_to_pod(local_path, remote_path):
    """Copy file to RunPod pod"""
    scp_cmd = f'scp -i {SSH_KEY} {local_path} {RUNPOD_HOST}:{remote_path}'
    print(f"Copying {local_path} to {remote_path}")
    result = subprocess.run(scp_cmd, shell=True)
    return result.returncode == 0

def deploy_pipeline():
    """Deploy the AI pipeline to RunPod pod"""
    
    print("🚀 Deploying Modomo AI Pipeline to RunPod Pod...")
    
    # 1. Copy handler file
    if not copy_file_to_pod("runpod-project/handler.py", "/workspace/handler.py"):
        print("❌ Failed to copy handler file")
        return False
    
    # 2. Install dependencies
    dependencies = [
        "transformers>=4.30.0",
        "ultralytics>=8.0.0", 
        "sam2>=0.4.0",
        "clip-by-openai>=1.0",
        "timm>=0.9.0",
        "einops>=0.6.0",
        "ftfy>=6.1.0",
        "regex>=2022.7.0"
    ]
    
    install_cmd = f"cd /workspace && pip install --no-cache-dir {' '.join(dependencies)}"
    if not run_ssh_command(install_cmd):
        print("❌ Failed to install dependencies")
        return False
    
    # 3. Test the handler
    test_cmd = "cd /workspace && python -c 'import handler; print(\"Handler loaded successfully\")'"
    if not run_ssh_command(test_cmd):
        print("❌ Handler test failed")
        return False
    
    # 4. Start the serverless handler
    start_cmd = "cd /workspace && nohup python -u handler.py > handler.log 2>&1 &"
    if not run_ssh_command(start_cmd):
        print("❌ Failed to start handler")
        return False
        
    print("✅ Deployment completed successfully!")
    print("📝 Check logs with: ssh -i ~/.ssh/id_ed25519 i4mc5gqc7sepzc-644112d0@ssh.runpod.io 'tail -f /workspace/handler.log'")
    return True

if __name__ == "__main__":
    if not deploy_pipeline():
        sys.exit(1)
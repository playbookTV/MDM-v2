#!/bin/bash

# RunPod Persistent Setup Script
# This script sets up a persistent environment for the MDM project on RunPod

set -e

echo "🚀 Setting up persistent MDM environment on RunPod..."

# Create persistent directories in /workspace (persistent storage on RunPod)
mkdir -p /workspace/MDM
mkdir -p /workspace/python_envs
mkdir -p /workspace/logs

# Copy project files to persistent storage if not already there
if [ ! -d "/workspace/MDM/backend" ]; then
    echo "📁 Copying project files to persistent storage..."
    cp -r /Users/leslieisah/MDM/* /workspace/MDM/
fi

# Create symbolic link from original location to persistent storage
if [ ! -L "/Users/leslieisah/MDM" ]; then
    echo "🔗 Creating symbolic link to persistent storage..."
    rm -rf /Users/leslieisah/MDM
    ln -s /workspace/MDM /Users/leslieisah/MDM
fi

# Set up Python virtual environment in persistent storage
cd /workspace/python_envs

if [ ! -d "mdm_env" ]; then
    echo "🐍 Creating persistent Python virtual environment..."
    python3 -m venv mdm_env
fi

# Activate virtual environment
source mdm_env/bin/activate

# Install Python dependencies for backend
echo "📦 Installing Python dependencies..."
cd /workspace/MDM/backend
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies if they exist
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

# Set up Node.js environment in persistent storage (if react-app exists)
if [ -d "/workspace/MDM/react-app" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd /workspace/MDM/react-app
    
    # Install pnpm if not available
    if ! command -v pnpm &> /dev/null; then
        npm install -g pnpm
    fi
    
    pnpm install
fi

# Create startup script for Jupyter notebook
cat > /workspace/start_mdm_server.py << 'EOF'
#!/usr/bin/env python3
"""
Startup script for MDM FastAPI server in Jupyter notebook environment
"""
import os
import sys
import subprocess

# Activate persistent virtual environment
activate_script = "/workspace/python_envs/mdm_env/bin/activate"
if os.path.exists(activate_script):
    # Source the virtual environment
    os.system(f"source {activate_script}")

# Change to backend directory
os.chdir("/workspace/MDM/backend")

# Add the backend directory to Python path
sys.path.insert(0, "/workspace/MDM/backend")

print("🚀 Starting MDM FastAPI server from persistent storage...")
print("📁 Working directory:", os.getcwd())
print("🐍 Python executable:", sys.executable)

# Import and run the FastAPI app
try:
    import uvicorn
    from main import app
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Installing missing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn", "fastapi"])
    
    # Try again
    import uvicorn
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
EOF

chmod +x /workspace/start_mdm_server.py

# Create environment activation script
cat > /workspace/activate_mdm.sh << 'EOF'
#!/bin/bash
# Activate MDM environment
source /workspace/python_envs/mdm_env/bin/activate
cd /workspace/MDM
echo "🎯 MDM environment activated!"
echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo ""
echo "Available commands:"
echo "  • Backend server: cd backend && python main.py"
echo "  • React app: cd react-app && pnpm run dev"
echo "  • TUI: cd TUI && PYTHONPATH=/workspace/MDM/TUI/src python -m modomo_tui.main"
EOF

chmod +x /workspace/activate_mdm.sh

echo "✅ Persistent environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Run: source /workspace/activate_mdm.sh"
echo "2. For Jupyter: exec(open('/workspace/start_mdm_server.py').read())"
echo "3. Or manually: cd /workspace/MDM/backend && python main.py"
echo ""
echo "📁 All files are now in persistent storage at /workspace/MDM"
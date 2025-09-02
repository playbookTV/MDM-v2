"""
RunPod Jupyter Startup Script
Run this in your Jupyter notebook to start the MDM server from persistent storage
"""

import os
import sys
import subprocess

def setup_persistent_environment():
    """Set up the persistent environment if not already done"""
    print("🔧 Setting up persistent environment...")
    
    # Run the setup script
    setup_script = "/workspace/MDM/runpod_setup.sh"
    if os.path.exists(setup_script):
        os.system(f"bash {setup_script}")
    else:
        print("❌ Setup script not found. Please run the initial setup first.")
        return False
    
    return True

def activate_environment():
    """Activate the persistent virtual environment"""
    print("🐍 Activating persistent virtual environment...")
    
    # Activate virtual environment by modifying sys.path
    venv_site_packages = "/workspace/python_envs/mdm_env/lib/python3.11/site-packages"
    if os.path.exists(venv_site_packages):
        sys.path.insert(0, venv_site_packages)
        
    # Set environment variables
    os.environ['VIRTUAL_ENV'] = "/workspace/python_envs/mdm_env"
    os.environ['PATH'] = f"/workspace/python_envs/mdm_env/bin:{os.environ.get('PATH', '')}"
    
    # Change to project directory
    os.chdir("/workspace/MDM")
    print(f"📁 Changed to: {os.getcwd()}")

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting MDM FastAPI server...")
    
    # Change to backend directory
    os.chdir("/workspace/MDM/backend")
    
    # Add backend to Python path
    sys.path.insert(0, "/workspace/MDM/backend")
    
    try:
        # Import FastAPI app
        from main import app
        import uvicorn
        
        print("✅ Successfully imported FastAPI app")
        print("🌐 Starting server on http://0.0.0.0:8000")
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload in Jupyter
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("🔧 Trying to install missing dependencies...")
        
        # Install missing dependencies
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "uvicorn", "fastapi", "sqlalchemy", "pydantic"
        ])
        
        print("🔄 Retrying server startup...")
        from main import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

# Main execution
if __name__ == "__main__":
    print("🎯 RunPod MDM Server Startup")
    print("=" * 40)
    
    # Check if we're in persistent storage
    if not os.path.exists("/workspace"):
        print("❌ /workspace directory not found. Are you running on RunPod?")
        sys.exit(1)
    
    # Set up environment if needed
    if not os.path.exists("/workspace/MDM"):
        if not setup_persistent_environment():
            sys.exit(1)
    
    # Activate environment
    activate_environment()
    
    # Start server
    start_server()

# For Jupyter notebook usage:
def start_mdm_server():
    """Convenience function to start the server from Jupyter"""
    print("🎯 Starting MDM server from Jupyter notebook...")
    
    # Activate environment
    activate_environment()
    
    # Start server in background (non-blocking)
    os.chdir("/workspace/MDM/backend")
    sys.path.insert(0, "/workspace/MDM/backend")
    
    try:
        from main import app
        import uvicorn
        
        print("✅ FastAPI app loaded successfully")
        print("🌐 Access your server at: http://localhost:8000")
        print("📊 API docs available at: http://localhost:8000/docs")
        
        # Start server (this will block the cell)
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True
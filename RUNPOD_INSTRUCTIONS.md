# RunPod Persistent Setup Instructions

This guide helps you set up the MDM project to persist across RunPod restarts by using `/workspace` (persistent storage).

## Quick Setup

### 1. Initial Setup (Run once)
```bash
# Make setup script executable
chmod +x /Users/leslieisah/MDM/runpod_setup.sh

# Run the setup script
bash /Users/leslieisah/MDM/runpod_setup.sh
```

### 2. For Jupyter Notebooks

**Option A: Simple startup (recommended)**
```python
# Copy this into a Jupyter cell and run it
exec(open('/workspace/MDM/runpod_jupyter_startup.py').read())

# Or use the convenience function
from runpod_jupyter_startup import start_mdm_server
start_mdm_server()
```

**Option B: Manual commands**
```python
import os
import sys

# Activate persistent environment
os.chdir('/workspace/MDM/backend')
sys.path.insert(0, '/workspace/python_envs/mdm_env/lib/python3.11/site-packages')
sys.path.insert(0, '/workspace/MDM/backend')

# Start server
from main import app
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. For Terminal/SSH

```bash
# Activate environment
source /workspace/activate_mdm.sh

# Start backend server
cd /workspace/MDM/backend
python main.py

# Or start React app
cd /workspace/MDM/react-app
pnpm run dev

# Or start TUI
cd /workspace/MDM/TUI
PYTHONPATH=/workspace/MDM/TUI/src python -m modomo_tui.main
```

## What Gets Persisted

- ✅ **Python virtual environment** → `/workspace/python_envs/mdm_env/`
- ✅ **Project files** → `/workspace/MDM/`
- ✅ **Node.js dependencies** → `/workspace/MDM/react-app/node_modules/`
- ✅ **Python packages** → Installed in persistent venv
- ✅ **Configuration files** → All moved to `/workspace/`

## Directory Structure

```
/workspace/
├── MDM/                          # Your project files (persistent)
│   ├── backend/
│   ├── react-app/
│   ├── TUI/
│   └── ...
├── python_envs/                  # Python virtual environments
│   └── mdm_env/                 # MDM Python environment
├── logs/                        # Application logs
├── start_mdm_server.py          # Jupyter startup script
└── activate_mdm.sh              # Environment activation script
```

## Access URLs

Once the server is running:
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **React App** (if running): http://localhost:3000

## Troubleshooting

### Missing Dependencies
```python
import subprocess
import sys
subprocess.run([sys.executable, "-m", "pip", "install", "package_name"])
```

### Reset Environment
```bash
rm -rf /workspace/MDM /workspace/python_envs
bash /Users/leslieisah/MDM/runpod_setup.sh
```

### Check Environment
```python
import os, sys
print("Working directory:", os.getcwd())
print("Python path:", sys.path[:3])
print("Virtual env:", os.environ.get('VIRTUAL_ENV', 'None'))
```

## Benefits

✅ **Persistent installations** - No need to reinstall packages after restart  
✅ **Fast startup** - Skip dependency installation  
✅ **Preserved configurations** - All settings maintain across sessions  
✅ **Multiple access methods** - Jupyter, terminal, or direct Python  
✅ **Automatic environment** - Everything configured automatically
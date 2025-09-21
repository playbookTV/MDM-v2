#!/usr/bin/env python3
"""
Fix UUID serialization issue in RunPod client
"""

import os
import sys
import json
import uuid
from typing import Any, Dict

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def uuid_serializer(obj):
    """Custom JSON serializer that handles UUID objects"""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, (list, tuple)):
        return [uuid_serializer(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: uuid_serializer(value) for key, value in obj.items()}
    else:
        return obj

def create_fixed_runpod_client():
    """Create the fixed RunPod client code"""
    
    # Read the current RunPod client
    with open('/Users/leslieisah/MDM/backend/app/services/runpod_client.py', 'r') as f:
        content = f.read()
    
    # Add the UUID import if not present
    if 'import json' not in content:
        content = content.replace('import httpx', 'import json\nimport httpx')
    
    if 'import uuid' not in content:
        content = content.replace('import json', 'import json\nimport uuid')
    
    # Add the UUID serializer function
    uuid_serializer_code = '''
def _serialize_uuids(obj):
    """Custom JSON serializer that handles UUID objects"""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, (list, tuple)):
        return [_serialize_uuids(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _serialize_uuids(value) for key, value in obj.items()}
    else:
        return obj

'''
    
    # Insert the serializer function after the class definition
    class_def_pos = content.find('class RunPodClient:')
    if class_def_pos != -1:
        # Insert before the class
        content = content[:class_def_pos] + uuid_serializer_code + content[class_def_pos:]
    
    # Fix the JSON serialization in _request_serverless_endpoint
    old_json_line = '                json=payload.get("input", {}),  # Send just the input data'
    new_json_line = '                json=_serialize_uuids(payload.get("input", {})),  # Send just the input data, handling UUIDs'
    
    content = content.replace(old_json_line, new_json_line)
    
    # Also fix the other endpoint method
    old_json_line2 = '                json=payload,'
    new_json_line2 = '                json=_serialize_uuids(payload),'
    
    content = content.replace(old_json_line2, new_json_line2)
    
    return content

def main():
    """Apply the UUID serialization fix"""
    print("🔧 Fixing UUID serialization in RunPod client")
    print("=" * 60)
    
    try:
        # Create the fixed content
        fixed_content = create_fixed_runpod_client()
        
        # Write the fixed content
        with open('/Users/leslieisah/MDM/backend/app/services/runpod_client.py', 'w') as f:
            f.write(fixed_content)
        
        print("✅ UUID serialization fix applied successfully")
        print("📝 Changes made:")
        print("   - Added UUID import")
        print("   - Added _serialize_uuids() helper function")
        print("   - Fixed JSON serialization in _request_serverless_endpoint()")
        print("   - Fixed JSON serialization in _request_custom_endpoint()")
        
        print("\n🎯 Next steps:")
        print("1. Restart the Celery worker to pick up changes:")
        print("   pkill -f celery && ./scripts/start_celery_worker.sh")
        print("2. Try processing the dataset again")
        print("3. Monitor job progress in the UI")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Simple test script for Roboflow dataset download
"""

import os
import sys
from roboflow import Roboflow

def test_roboflow_download():
    """Test basic Roboflow dataset download"""
    
    # Test URLs - these are public datasets from Roboflow Universe
    test_urls = [
        "https://universe.roboflow.com/roboflow-100/furniture-ngpea",
        "https://universe.roboflow.com/roboflow-jvuqo/coco-128",
    ]
    
    # Get API key from environment
    api_key = os.getenv("ROBOFLOW_API_KEY")
    if not api_key:
        print("⚠️  ROBOFLOW_API_KEY not set in environment")
        print("   Please set it with: export ROBOFLOW_API_KEY='your_key'")
        print("   Get your key from: https://app.roboflow.com/settings/api")
        return False
    
    print(f"✅ Found API key: {api_key[:10]}...")
    
    try:
        # Initialize Roboflow
        rf = Roboflow(api_key=api_key)
        print("✅ Roboflow client initialized")
        
        # Test URL parsing
        for url in test_urls:
            print(f"\n🔍 Testing URL: {url}")
            
            # Parse the URL to get workspace, project, version
            parts = url.replace("https://universe.roboflow.com/", "").split("/")
            if len(parts) >= 2:
                workspace = parts[0]
                project = parts[1]
                version = 1  # Default to version 1
                
                print(f"   Workspace: {workspace}")
                print(f"   Project: {project}")
                print(f"   Version: {version}")
                
                try:
                    # Try to access the project
                    rf_workspace = rf.workspace(workspace)
                    rf_project = rf_workspace.project(project)
                    rf_version = rf_project.version(version)
                    
                    print(f"   ✅ Successfully accessed project")
                    
                    # Try to download (just get info, not full download)
                    print(f"   📥 Attempting download...")
                    dataset = rf_version.download("coco", location="./temp_test")
                    
                    if dataset:
                        print(f"   ✅ Download successful!")
                        print(f"   📁 Location: {dataset.location if hasattr(dataset, 'location') else 'Unknown'}")
                        
                        # Clean up
                        import shutil
                        if os.path.exists("./temp_test"):
                            shutil.rmtree("./temp_test")
                            print(f"   🧹 Cleaned up temp files")
                    else:
                        print(f"   ❌ Download returned None")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Roboflow Download Test")
    print("=" * 50)
    
    success = test_roboflow_download()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed")
    else:
        print("❌ Test failed")
    
    sys.exit(0 if success else 1)
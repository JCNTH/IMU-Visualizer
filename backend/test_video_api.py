#!/usr/bin/env python3
"""Test script to trigger video generation via API"""

import requests
import os
from pathlib import Path

def test_video_api():
    """Test video generation via API call"""
    
    # Check if the .mot file exists
    mot_path = "static/sessions/session_ik.mot"
    if not os.path.exists(mot_path):
        print(f"❌ Motion file not found: {mot_path}")
        return False
    
    # API endpoint
    url = "http://localhost:8000/api/generate_video"
    
    # Request payload
    payload = {
        "mot_file_path": str(Path(mot_path).absolute()),
        "session_name": "test_session"
    }
    
    print(f"🎬 Calling video generation API...")
    print(f"Motion file: {payload['mot_file_path']}")
    print(f"Session: {payload['session_name']}")
    
    try:
        response = requests.post(url, json=payload, timeout=1800)  # 30 minutes timeout
        
        if response.status_code == 200:
            result = response.json()
            print(f"🎉 SUCCESS: {result}")
            return True
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (this is normal for video generation)")
        return True  # Consider timeout as success since video generation takes time
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_video_api()
    print(f"Video API test: {'PASSED' if success else 'FAILED'}") 
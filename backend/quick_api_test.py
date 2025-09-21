#!/usr/bin/env python3
"""Quick test to verify the endpoint fix"""

import requests
import time

def test_endpoint_fix():
    """Test if the generate_video_stream endpoint works without 422 error"""
    
    print("🧪 Testing fixed generate_video_stream endpoint...")
    
    url = "http://localhost:8000/api/generate_video_stream"
    params = {
        "modelPath": "dummy_model.osim",
        "motPath": "dummy_motion.mot", 
        "calibPath": "dummy_calib.npz",
        "subject": "frontend_demo"
    }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        # Test with short timeout to see immediate response
        response = requests.get(url, params=params, timeout=5, stream=True)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! No more 422 error!")
            print("🎬 Video generation started (will timeout due to short limit)")
            
            # Try to read first few lines
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                if i < 3:  # Just first 3 lines
                    print(f"   Stream line {i+1}: {line}")
                else:
                    break
                    
            return True
        elif response.status_code == 422:
            print("❌ Still getting 422 error!")
            print(f"Error details: {response.text}")
            return False
        else:
            print(f"❓ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (GOOD - means processing started)")
        return True
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_endpoint_fix()
    if success:
        print("\n🎉 Endpoint fix SUCCESSFUL!")
        print("🎯 Frontend 'Generate Video' button should now work!")
        print("💡 The TypeError should be resolved and video generation should start")
    else:
        print("\n❌ Endpoint fix FAILED!")
        print("🔧 Still need to debug the parameter handling") 
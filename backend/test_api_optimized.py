#!/usr/bin/env python3
"""Test optimized video generation via API with different speed settings"""

import requests
import os
import time
from pathlib import Path

def test_optimized_api():
    """Test the video generation API with optimization parameters"""
    
    # Check if .mot file exists
    mot_path = Path("static/sessions/session_ik.mot").absolute()
    if not mot_path.exists():
        print(f"❌ Motion file not found: {mot_path}")
        return False
    
    print("🎬 Testing optimized video generation API...")
    print(f"Motion file: {mot_path}")
    
    # API endpoint
    url = "http://localhost:8000/api/generate_video"
    
    # Test different optimization levels
    configs = [
        {
            "name": "🚀 ULTRA FAST (5 sec, 4x speed)",
            "payload": {
                "mot_file_path": str(mot_path),
                "session_name": "ultra_fast_test",
                "start_frame": 0,
                "end_frame": 150,        # ~5 seconds
                "skip_frames": 4,        # 4x speed
                "resolution": [320, 180], # Very small
                "fps": 10
            }
        },
        {
            "name": "⚡ FAST (15 sec, 2x speed)", 
            "payload": {
                "mot_file_path": str(mot_path),
                "session_name": "fast_test",
                "start_frame": 0,
                "end_frame": 450,        # ~15 seconds
                "skip_frames": 2,        # 2x speed
                "resolution": [480, 270], # Quarter HD
                "fps": 15
            }
        }
    ]
    
    for config in configs:
        print(f"\n{config['name']}")
        print(f"  Parameters: {config['payload']}")
        
        start_time = time.time()
        
        try:
            response = requests.post(url, json=config['payload'], timeout=600)  # 10 min timeout
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ SUCCESS in {duration:.1f}s")
                print(f"  📹 Result: {result}")
                
                # Check if video file was created
                if 'video_path' in result.get('ik_results', {}):
                    video_path = result['ik_results']['video_path']
                    if os.path.exists(video_path):
                        file_size = os.path.getsize(video_path) / (1024 * 1024)
                        print(f"  📦 Video size: {file_size:.2f} MB")
                    
            else:
                print(f"  ❌ API Error {response.status_code} after {duration:.1f}s")
                print(f"  Details: {response.text}")
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time  
            print(f"  ⏰ Timeout after {duration:.1f}s (this might be normal for video generation)")
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Request failed after {duration:.1f}s: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Quick API test for the frontend:")
    print(f"   POST http://localhost:8000/api/generate_video")
    print(f"   JSON payload:")
    print(f"   {{")
    print(f"     \"mot_file_path\": \"{mot_path}\",")
    print(f"     \"session_name\": \"demo\",")
    print(f"     \"start_frame\": 0,")
    print(f"     \"end_frame\": 150,")
    print(f"     \"skip_frames\": 4,")
    print(f"     \"resolution\": [320, 180],")
    print(f"     \"fps\": 10")
    print(f"   }}")

if __name__ == "__main__":
    test_optimized_api() 
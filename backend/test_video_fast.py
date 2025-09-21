#!/usr/bin/env python3
"""Test optimized IMU video generation with different speed settings"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.osim2video_imu import generate_imu_video

def test_video_speeds():
    """Test video generation with different optimization levels"""
    
    # Check required files
    model_path = "static/models/default_model.osim"
    motion_path = "static/sessions/session_ik.mot"
    calib_path = "static/models/default_calib.npz"
    geometry_path = "static/models/Geometry"
    
    for path, name in [(model_path, "Model"), (motion_path, "Motion"), 
                       (calib_path, "Calibration"), (geometry_path, "Geometry")]:
        if not os.path.exists(path):
            print(f"❌ {name} file not found: {path}")
            return False
    
    print("🎬 Testing different video generation speeds...")
    print("=" * 60)
    
    # Test configurations from fastest to slowest
    configs = [
        {
            "name": "🚀 ULTRA FAST (10 sec demo)",
            "start_frame": 0,
            "end_frame": 150,        # ~5 seconds of motion
            "skip_frames": 4,        # Skip 3 frames (4x speed)
            "resolution": (320, 180), # Very small
            "fps": 10,
            "output": "static/sessions/video_ultra_fast.mp4"
        },
        {
            "name": "⚡ FAST (30 sec demo)", 
            "start_frame": 0,
            "end_frame": 450,        # ~15 seconds of motion
            "skip_frames": 2,        # Skip 1 frame (2x speed)
            "resolution": (480, 270), # Quarter HD
            "fps": 15,
            "output": "static/sessions/video_fast.mp4"
        },
        {
            "name": "🎯 BALANCED (1 min demo)",
            "start_frame": 0,
            "end_frame": 900,        # ~30 seconds of motion
            "skip_frames": 1,        # No skipping
            "resolution": (720, 405), # Half HD
            "fps": 20,
            "output": "static/sessions/video_balanced.mp4"
        }
    ]
    
    for config in configs:
        print(f"\n{config['name']}")
        print(f"  Frames: {config['start_frame']} to {config['end_frame']}")
        print(f"  Skip: every {config['skip_frames']} frames")
        print(f"  Resolution: {config['resolution']}")
        print(f"  FPS: {config['fps']}")
        
        start_time = time.time()
        
        try:
            video_path = generate_imu_video(
                osim_path=model_path,
                motion_path=motion_path,
                calib_path=calib_path,
                output_video_path=config["output"],
                geometry_path=geometry_path,
                start_frame=config["start_frame"],
                end_frame=config["end_frame"],
                skip_frames=config["skip_frames"],
                resolution=config["resolution"],
                fps=config["fps"]
            )
            
            duration = time.time() - start_time
            file_size = os.path.getsize(video_path) / (1024 * 1024) if os.path.exists(video_path) else 0
            
            print(f"  ✅ SUCCESS in {duration:.1f}s")
            print(f"  📹 Output: {video_path}")
            print(f"  📦 Size: {file_size:.2f} MB")
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ FAILED after {duration:.1f}s: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Video generation tests complete!")
    print(f"💡 For fastest results, use:")
    print(f"   - start_frame=0, end_frame=150")
    print(f"   - skip_frames=4 (4x speed)")
    print(f"   - resolution=(320,180)")
    print(f"   - fps=10")

if __name__ == "__main__":
    test_video_speeds() 
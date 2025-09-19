#!/usr/bin/env python3
"""Test script for IMU video generation"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import the utilities
sys.path.append(str(Path(__file__).parent / "src"))

from utils.osim2video_imu import generate_imu_video

def test_video_generation():
    """Test the IMU video generation with current files"""
    
    # Paths to our files
    model_path = "static/models/default_model.osim"
    motion_path = "static/sessions/session_ik.mot"
    calib_path = "static/models/default_calib.npz"
    geometry_path = "static/models/Geometry"
    
    # Output video path
    output_video = "static/sessions/test_imu_video.mp4"
    output_dir = "static/sessions/frames"
    
    # Check if all required files exist
    for path, name in [(model_path, "Model"), (motion_path, "Motion"), (calib_path, "Calibration")]:
        if not os.path.exists(path):
            print(f"ERROR: {name} file not found: {path}")
            return False
    
    if not os.path.exists(geometry_path):
        print(f"ERROR: Geometry directory not found: {geometry_path}")
        return False
    
    print(f"✅ All required files found")
    print(f"Model: {model_path}")
    print(f"Motion: {motion_path}")
    print(f"Calibration: {calib_path}")
    print(f"Geometry: {geometry_path}")
    print()
    
    try:
        print("🎬 Starting IMU video generation...")
        video_path = generate_imu_video(
            osim_path=model_path,
            motion_path=motion_path,
            calib_path=calib_path,
            output_video_path=output_video,
            geometry_path=geometry_path,
            output_dir=output_dir
        )
        
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            print(f"🎉 SUCCESS: Video generated at {video_path}")
            print(f"📹 Video size: {file_size:.2f} MB")
            return True
        else:
            print(f"❌ ERROR: Video file not created at {video_path}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Video generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_video_generation()
    sys.exit(0 if success else 1) 
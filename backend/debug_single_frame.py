#!/usr/bin/env python3
"""Debug single frame rendering to identify video generation issues"""

import os
import sys
from pathlib import Path
import numpy as np

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.osim2video_imu import generate_imu_video

def debug_single_frame():
    """Generate just one frame for debugging"""
    
    # Check required files
    model_path = "static/models/default_model.osim"
    motion_path = "static/sessions/session_ik.mot" 
    calib_path = "static/models/default_calib.npz"
    geometry_path = "static/models/Geometry"
    
    for path, name in [(model_path, "Model"), (motion_path, "Motion"), 
                       (calib_path, "Calibration")]:
        if not os.path.exists(path):
            print(f"❌ {name} file not found: {path}")
            return False
    
    if not os.path.exists(geometry_path):
        print(f"❌ Geometry directory not found: {geometry_path}")
        return False
    
    print("🔍 DEBUG: Testing single frame generation...")
    print(f"Model: {model_path}")
    print(f"Motion: {motion_path}")
    print(f"Calibration: {calib_path}")
    print(f"Geometry: {geometry_path}")
    
    try:
        # Test with very small range - just first 3 frames
        video_path = generate_imu_video(
            osim_path=model_path,
            motion_path=motion_path,
            calib_path=calib_path,
            output_video_path="static/sessions/debug_single_frame.mp4",
            geometry_path=geometry_path,
            start_frame=0,
            end_frame=3,        # Just 3 frames
            skip_frames=1,      # No skipping
            resolution=(480, 270),  # Small resolution
            fps=10
        )
        
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / 1024  # KB
            print(f"✅ Debug video created: {video_path}")
            print(f"📦 Size: {file_size:.1f} KB")
            
            # Check if OBJ frames were created
            frames_dir = Path("static/sessions/frames")
            if frames_dir.exists():
                obj_files = list(frames_dir.glob("*.obj"))
                print(f"📁 OBJ frames created: {len(obj_files)}")
                
                # Examine first OBJ file
                if obj_files:
                    first_obj = obj_files[0]
                    with open(first_obj, 'r') as f:
                        lines = f.readlines()
                    vertices = [line for line in lines if line.startswith('v ')]
                    faces = [line for line in lines if line.startswith('f ')]
                    print(f"📋 First OBJ file ({first_obj.name}):")
                    print(f"   Vertices: {len(vertices)}")
                    print(f"   Faces: {len(faces)}")
                    
                    if len(vertices) > 0:
                        print(f"   Sample vertices:")
                        for i, v in enumerate(vertices[:3]):
                            print(f"     {v.strip()}")
                    else:
                        print("   ⚠️  No vertices found in OBJ file!")
            
            return True
        else:
            print(f"❌ Video file not created: {video_path}")
            return False
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_single_frame()
    if success:
        print("\n✅ Single frame debug completed successfully!")
        print("🎯 Next steps:")
        print("   1. Check the debug video file")
        print("   2. Examine the OBJ files in static/sessions/frames/")
        print("   3. Verify mesh geometry is being loaded correctly")
    else:
        print("\n❌ Single frame debug failed!")
        print("🔧 Check the error messages above for clues") 
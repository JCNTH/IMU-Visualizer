#!/usr/bin/env python3
"""Test the working obj2video.py script with our files"""

import os
import sys
import shutil
from pathlib import Path

def test_obj2video():
    """Test if the obj2video.py script works with our setup"""
    
    # Copy obj2video.py to our backend if it doesn't exist
    backend_dir = Path(__file__).parent
    obj2video_path = backend_dir / "obj2video.py"
    source_obj2video = Path("/Users/julianng-thow-hing/Desktop/mbl_osim2obj/obj2video.py")
    
    if not obj2video_path.exists() and source_obj2video.exists():
        print(f"📋 Copying obj2video.py from {source_obj2video}")
        shutil.copy2(source_obj2video, obj2video_path)
    
    # Check required files
    calib_path = "static/models/default_calib.npz"
    frames_dir = Path("static/sessions/frames")
    
    if not os.path.exists(calib_path):
        print(f"❌ Calibration file not found: {calib_path}")
        return False
    
    if not frames_dir.exists() or len(list(frames_dir.glob("*.obj"))) == 0:
        print(f"❌ No OBJ frames found in: {frames_dir}")
        print("💡 Run debug_single_frame.py first to generate OBJ files")
        return False
    
    obj_files = list(frames_dir.glob("*.obj"))
    print(f"✅ Found {len(obj_files)} OBJ files in {frames_dir}")
    
    # Test with obj2video.py
    output_video = "static/sessions/test_obj2video.mp4"
    
    try:
        import subprocess
        cmd = [
            "python", str(obj2video_path),
            "--obj", str(frames_dir),
            "--calib", calib_path,
            "--output", output_video,
            "--width", "480",
            "--height", "270",
            "--fps", "10"
        ]
        
        print(f"🎬 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=backend_dir)
        
        if result.returncode == 0:
            if os.path.exists(output_video):
                file_size = os.path.getsize(output_video) / 1024  # KB
                print(f"✅ obj2video.py SUCCESS!")
                print(f"📹 Video: {output_video}")
                print(f"📦 Size: {file_size:.1f} KB")
                print(f"🎯 This proves the OBJ files are valid!")
                return True
            else:
                print(f"❌ Video not created: {output_video}")
        else:
            print(f"❌ obj2video.py failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error running obj2video.py: {e}")
    
    return False

if __name__ == "__main__":
    success = test_obj2video()
    if success:
        print("\n🎉 obj2video.py works! The issue is in our rendering pipeline.")
        print("🔧 Focus on fixing the render_combined_frame() function.")
    else:
        print("\n❌ obj2video.py test failed.")
        print("🔍 Check if OBJ files exist and contain valid geometry.") 
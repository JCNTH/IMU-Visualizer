#!/usr/bin/env python3
"""Test video generation with the complete MOT file"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.osim2video_imu import generate_imu_video

def test_video_with_complete_mot():
    """Test video generation using the complete MOT file with all required columns"""
    
    print("🎬 Testing video generation with COMPLETE MOT file...")
    
    # Use the complete MOT file we just generated
    model_path = "Model/LaiArnoldModified2017_poly_withArms_weldHand_scaled_adjusted.osim"
    motion_path = "static/sessions/session_ik_COMPLETE.mot"  # The complete one
    calib_path = "static/models/default_calib.npz"
    geometry_path = "./Model/Geometry"
    
    # Output video path
    output_video = "static/sessions/test_complete_video.mp4"
    output_dir = "static/sessions/complete_frames"
    
    # Check required files
    for path, name in [(model_path, "Model"), (motion_path, "Motion"), (calib_path, "Calibration")]:
        if not os.path.exists(path):
            print(f"❌ {name} file not found: {path}")
            return False
    
    if not os.path.exists(geometry_path):
        print(f"❌ Geometry directory not found: {geometry_path}")
        return False
    
    print(f"✅ All files found!")
    print(f"Model: {model_path}")
    print(f"Motion: {motion_path} (COMPLETE with pelvis position)")
    print(f"Calibration: {calib_path}")
    print(f"Geometry: {geometry_path}")
    
    try:
        print("🎬 Generating video with complete MOT data...")
        
        # Test with ultra-fast settings first
        video_path = generate_imu_video(
            osim_path=model_path,
            motion_path=motion_path,
            calib_path=calib_path,
            output_video_path=output_video,
            geometry_path=geometry_path,
            output_dir=output_dir,
            start_frame=0,
            end_frame=30,        # Just 30 frames for quick test
            skip_frames=1,       # No skipping
            resolution=(480, 270),
            fps=10
        )
        
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / 1024  # KB
            print(f"✅ Complete video generated: {video_path}")
            print(f"📦 Size: {file_size:.1f} KB")
            
            # Compare with previous blank video
            blank_video_path = "static/sessions/debug_single_frame.mp4"
            if os.path.exists(blank_video_path):
                blank_size = os.path.getsize(blank_video_path) / 1024
                print(f"📊 Comparison:")
                print(f"   Blank video (3 frames): {blank_size:.1f} KB")
                print(f"   Complete video (30 frames): {file_size:.1f} KB")
                print(f"   Size ratio: {file_size/blank_size:.1f}x larger")
                
                if file_size > blank_size * 5:  # Should be much larger
                    print(f"🎉 SUCCESS! Video is much larger - likely contains skeleton data!")
                else:
                    print(f"⚠️  Video size is still small - might still be blank")
            
            return True
        else:
            print(f"❌ Video file not created: {video_path}")
            return False
            
    except Exception as e:
        print(f"❌ Video generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_video_with_complete_mot()
    if success:
        print("\n🎉 Complete MOT video test SUCCESSFUL!")
        print("🎯 The skeleton should now be visible in the video!")
        print("💡 Check the output video file to verify")
    else:
        print("\n❌ Complete MOT video test FAILED!")
        print("🔧 The MOT file might still be missing data or have format issues") 
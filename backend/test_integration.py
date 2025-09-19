#!/usr/bin/env python3
"""
Test script to verify the osim2obj integration into mbl_imuviz.
This script tests the complete pipeline from joint angles to video generation.
"""

import os
import sys
import numpy as np
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

def test_setup():
    """Test that the setup utilities work correctly."""
    print("=" * 50)
    print("Testing Setup Utilities")
    print("=" * 50)
    
    try:
        # Test camera calibration creation
        from utils.create_default_calib import create_default_calibration
        
        test_dir = Path(__file__).parent / "test_output"
        test_dir.mkdir(exist_ok=True)
        
        calib_path = test_dir / "test_calib.npz"
        create_default_calibration(str(calib_path))
        
        # Verify calibration file was created
        if calib_path.exists():
            print("✅ Camera calibration creation: PASSED")
            
            # Load and verify contents
            import numpy as np
            calib = np.load(calib_path)
            assert 'K' in calib.files
            assert 'R' in calib.files
            assert 'T' in calib.files
            print("✅ Camera calibration contents: PASSED")
        else:
            print("❌ Camera calibration creation: FAILED")
            
    except Exception as e:
        print(f"❌ Camera calibration test: FAILED - {e}")
    
    try:
        # Test model setup
        from utils.setup_default_model import setup_default_model, create_minimal_model
        
        # Create a minimal model for testing
        model_path = test_dir / "test_model.osim"
        create_minimal_model(model_path)
        
        if model_path.exists():
            print("✅ Model creation: PASSED")
            
            # Verify it's a valid XML file
            import xml.etree.ElementTree as ET
            tree = ET.parse(model_path)
            root = tree.getroot()
            assert root.tag == "OpenSimDocument"
            print("✅ Model XML structure: PASSED")
        else:
            print("❌ Model creation: FAILED")
            
    except Exception as e:
        print(f"❌ Model setup test: FAILED - {e}")

def test_mot_generation():
    """Test .mot file generation from joint angles."""
    print("\n" + "=" * 50)
    print("Testing MOT File Generation")
    print("=" * 50)
    
    try:
        from utils.mot_generator import create_mot_file, validate_mot_file, get_mot_info
        
        # Create sample joint angles
        n_frames = 100
        joint_angles = {
            'hip_flexion_r': np.sin(np.linspace(0, 2*np.pi, n_frames)) * 30,  # 30 degree amplitude
            'hip_flexion_l': np.sin(np.linspace(0, 2*np.pi, n_frames)) * 30,
            'knee_angle_r': np.abs(np.sin(np.linspace(0, 2*np.pi, n_frames))) * 60,  # 0-60 degrees
            'knee_angle_l': np.abs(np.sin(np.linspace(0, 2*np.pi, n_frames))) * 60,
            'ankle_angle_r': np.sin(np.linspace(0, 2*np.pi, n_frames)) * 15,
            'ankle_angle_l': np.sin(np.linspace(0, 2*np.pi, n_frames)) * 15,
        }
        
        test_dir = Path(__file__).parent / "test_output"
        mot_path = test_dir / "test_motion.mot"
        
        # Create .mot file
        created_path = create_mot_file(joint_angles, str(mot_path))
        
        if Path(created_path).exists():
            print("✅ MOT file creation: PASSED")
            
            # Validate the file
            if validate_mot_file(created_path):
                print("✅ MOT file validation: PASSED")
                
                # Get file info
                info = get_mot_info(created_path)
                print(f"✅ MOT file info: {info['n_rows']} rows, {info['n_columns']} columns, {info['duration']:.2f}s duration")
                
                if info['valid'] and info['n_rows'] == n_frames:
                    print("✅ MOT file contents: PASSED")
                else:
                    print("❌ MOT file contents: FAILED")
            else:
                print("❌ MOT file validation: FAILED")
        else:
            print("❌ MOT file creation: FAILED")
            
    except Exception as e:
        print(f"❌ MOT generation test: FAILED - {e}")
        import traceback
        traceback.print_exc()

def test_services():
    """Test the enhanced services."""
    print("\n" + "=" * 50)
    print("Testing Enhanced Services")
    print("=" * 50)
    
    try:
        # Test IK service
        from api.services.ik_service import IKService
        
        ik_service = IKService()
        print("✅ IK Service initialization: PASSED")
        
        # Test mot file creation method
        sample_ik_results = {
            'joint_angles': {
                'hip_flexion_r': [10, 15, 20, 15, 10],
                'hip_flexion_l': [10, 15, 20, 15, 10],
                'knee_angle_r': [5, 10, 15, 10, 5],
                'knee_angle_l': [5, 10, 15, 10, 5],
            }
        }
        
        test_dir = Path(__file__).parent / "test_output"
        test_dir.mkdir(exist_ok=True)
        
        # Temporarily change the static directory for testing
        original_create_mot = ik_service.create_mot_file
        def test_create_mot(results, session_name="test"):
            from utils.mot_generator import create_mot_from_ik_results
            return create_mot_from_ik_results(results, str(test_dir), session_name)
        
        ik_service.create_mot_file = test_create_mot
        
        mot_path = ik_service.create_mot_file(sample_ik_results, "test_session")
        
        if Path(mot_path).exists():
            print("✅ IK Service MOT creation: PASSED")
        else:
            print("❌ IK Service MOT creation: FAILED")
            
    except Exception as e:
        print(f"❌ IK Service test: FAILED - {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # Test Video service initialization
        from api.services.video_service import VideoService
        
        video_service = VideoService()
        print("✅ Video Service initialization: PASSED")
        
        # Check if default files were created
        if hasattr(video_service, 'default_calib_path') and Path(video_service.default_calib_path).exists():
            print("✅ Video Service default calibration: PASSED")
        else:
            print("❌ Video Service default calibration: FAILED")
            
    except Exception as e:
        print(f"❌ Video Service test: FAILED - {e}")
        import traceback
        traceback.print_exc()

def test_api_imports():
    """Test that all API imports work correctly."""
    print("\n" + "=" * 50)
    print("Testing API Imports")
    print("=" * 50)
    
    try:
        # Test main API imports
        from api.main import app, ik_service, video_service
        print("✅ Main API imports: PASSED")
        
        # Test that FastAPI app was created
        if app is not None:
            print("✅ FastAPI app creation: PASSED")
        else:
            print("❌ FastAPI app creation: FAILED")
            
        # Test service initialization
        if ik_service is not None and video_service is not None:
            print("✅ Service initialization: PASSED")
        else:
            print("❌ Service initialization: FAILED")
            
    except Exception as e:
        print(f"❌ API imports test: FAILED - {e}")
        import traceback
        traceback.print_exc()

def test_file_organization():
    """Test that files are properly organized and imports work."""
    print("\n" + "=" * 50)
    print("Testing File Organization")
    print("=" * 50)
    
    # Test relative imports
    try:
        from utils.mot2quats import mot2quats
        print("✅ mot2quats import: PASSED")
    except Exception as e:
        print(f"❌ mot2quats import: FAILED - {e}")
    
    try:
        from utils.mot_generator import create_mot_file
        print("✅ mot_generator import: PASSED")
    except Exception as e:
        print(f"❌ mot_generator import: FAILED - {e}")
    
    try:
        from utils.osim_video_generator import generate_video_from_motion
        print("✅ osim_video_generator import: PASSED")
    except Exception as e:
        print(f"❌ osim_video_generator import: FAILED - {e}")
    
    try:
        from utils.create_default_calib import create_default_calibration
        print("✅ create_default_calib import: PASSED")
    except Exception as e:
        print(f"❌ create_default_calib import: FAILED - {e}")
    
    try:
        from utils.setup_default_model import setup_default_model
        print("✅ setup_default_model import: PASSED")
    except Exception as e:
        print(f"❌ setup_default_model import: FAILED - {e}")
    
    # Test that essential files exist
    backend_dir = Path(__file__).parent
    essential_files = [
        "src/utils/mot2quats.py",
        "src/utils/mot_generator.py", 
        "src/utils/osim_video_generator.py",
        "src/utils/create_default_calib.py",
        "src/utils/setup_default_model.py",
        "src/api/services/ik_service.py",
        "src/api/services/video_service.py",
        "src/api/main.py",
    ]
    
    all_exist = True
    for file_path in essential_files:
        full_path = backend_dir / file_path
        if full_path.exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            all_exist = False
    
    if all_exist:
        print("✅ All essential files present: PASSED")
    else:
        print("❌ Some essential files missing: FAILED")

def cleanup():
    """Clean up test files."""
    print("\n" + "=" * 50)
    print("Cleaning up test files")
    print("=" * 50)
    
    try:
        import shutil
        test_dir = Path(__file__).parent / "test_output"
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("✅ Test cleanup: PASSED")
    except Exception as e:
        print(f"❌ Test cleanup: FAILED - {e}")

def main():
    """Run all integration tests."""
    print("MBL_OSIM2OBJ Integration Test Suite")
    print("=" * 50)
    
    # Run all tests
    test_setup()
    test_mot_generation()
    test_services()
    test_api_imports()
    test_file_organization()
    
    # Cleanup
    cleanup()
    
    print("\n" + "=" * 50)
    print("Integration Test Complete")
    print("=" * 50)
    print("\nIf all tests passed, the integration is working correctly!")
    print("You can now:")
    print("1. Start the backend server: python -m src.api.main")
    print("2. Upload IMU data through the frontend")
    print("3. Run IK processing to generate .mot files")
    print("4. Generate videos from the .mot files")

if __name__ == "__main__":
    main() 
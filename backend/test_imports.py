#!/usr/bin/env python3
"""
Simple test to verify all imports work correctly after the integration.
"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test all critical imports."""
    
    print("Testing imports...")
    
    try:
        # Test utils imports
        from utils.mot2quats import mot2quats
        print("✅ mot2quats import: OK")
    except Exception as e:
        print(f"❌ mot2quats import: FAILED - {e}")
    
    try:
        from utils.mot_generator import create_mot_file
        print("✅ mot_generator import: OK")
    except Exception as e:
        print(f"❌ mot_generator import: FAILED - {e}")
    
    try:
        from utils.osim_video_generator import generate_video_from_motion
        print("✅ osim_video_generator import: OK")
    except Exception as e:
        print(f"❌ osim_video_generator import: FAILED - {e}")
    
    try:
        from utils.create_default_calib import create_default_calibration
        print("✅ create_default_calib import: OK")
    except Exception as e:
        print(f"❌ create_default_calib import: FAILED - {e}")
    
    try:
        from utils.setup_default_model import setup_default_model
        print("✅ setup_default_model import: OK")
    except Exception as e:
        print(f"❌ setup_default_model import: FAILED - {e}")
    
    try:
        # Test constants imports
        from constants import constant_common, constant_mt, constant_mocap
        print("✅ constants import: OK")
    except Exception as e:
        print(f"❌ constants import: FAILED - {e}")
    
    try:
        # Test utils.common import
        from utils import common
        print("✅ utils.common import: OK")
    except Exception as e:
        print(f"❌ utils.common import: FAILED - {e}")
    
    try:
        # Test MT utils imports
        from utils.mt import preprocessing_mt, calibration_mt, ik_mt
        print("✅ MT utils import: OK")
    except Exception as e:
        print(f"❌ MT utils import: FAILED - {e}")
    
    try:
        # Test scripts import
        from scripts.run_mt import mt_ik_in_memory
        print("✅ run_mt import: OK")
    except Exception as e:
        print(f"❌ run_mt import: FAILED - {e}")
    
    try:
        # Test services imports
        from api.services.ik_service import IKService
        print("✅ IK service import: OK")
    except Exception as e:
        print(f"❌ IK service import: FAILED - {e}")
    
    try:
        from api.services.video_service import VideoService
        print("✅ Video service import: OK")
    except Exception as e:
        print(f"❌ Video service import: FAILED - {e}")
    
    try:
        # Test main API import
        from api.main import app
        print("✅ Main API import: OK")
    except Exception as e:
        print(f"❌ Main API import: FAILED - {e}")
    
    print("\nImport test completed!")

if __name__ == "__main__":
    test_imports() 
"""
Simple test to verify all imports work correctly after the integration.
"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test all critical imports."""
    
    print("Testing imports...")
    
    try:
        # Test utils imports
        from utils.mot2quats import mot2quats
        print("✅ mot2quats import: OK")
    except Exception as e:
        print(f"❌ mot2quats import: FAILED - {e}")
    
    try:
        from utils.mot_generator import create_mot_file
        print("✅ mot_generator import: OK")
    except Exception as e:
        print(f"❌ mot_generator import: FAILED - {e}")
    
    try:
        from utils.osim_video_generator import generate_video_from_motion
        print("✅ osim_video_generator import: OK")
    except Exception as e:
        print(f"❌ osim_video_generator import: FAILED - {e}")
    
    try:
        from utils.create_default_calib import create_default_calibration
        print("✅ create_default_calib import: OK")
    except Exception as e:
        print(f"❌ create_default_calib import: FAILED - {e}")
    
    try:
        from utils.setup_default_model import setup_default_model
        print("✅ setup_default_model import: OK")
    except Exception as e:
        print(f"❌ setup_default_model import: FAILED - {e}")
    
    try:
        # Test constants imports
        from constants import constant_common, constant_mt, constant_mocap
        print("✅ constants import: OK")
    except Exception as e:
        print(f"❌ constants import: FAILED - {e}")
    
    try:
        # Test utils.common import
        from utils import common
        print("✅ utils.common import: OK")
    except Exception as e:
        print(f"❌ utils.common import: FAILED - {e}")
    
    try:
        # Test MT utils imports
        from utils.mt import preprocessing_mt, calibration_mt, ik_mt
        print("✅ MT utils import: OK")
    except Exception as e:
        print(f"❌ MT utils import: FAILED - {e}")
    
    try:
        # Test scripts import
        from scripts.run_mt import mt_ik_in_memory
        print("✅ run_mt import: OK")
    except Exception as e:
        print(f"❌ run_mt import: FAILED - {e}")
    
    try:
        # Test services imports
        from api.services.ik_service import IKService
        print("✅ IK service import: OK")
    except Exception as e:
        print(f"❌ IK service import: FAILED - {e}")
    
    try:
        from api.services.video_service import VideoService
        print("✅ Video service import: OK")
    except Exception as e:
        print(f"❌ Video service import: FAILED - {e}")
    
    try:
        # Test main API import
        from api.main import app
        print("✅ Main API import: OK")
    except Exception as e:
        print(f"❌ Main API import: FAILED - {e}")
    
    print("\nImport test completed!")

if __name__ == "__main__":
    test_imports() 
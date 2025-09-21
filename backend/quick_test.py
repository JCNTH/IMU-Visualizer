#!/usr/bin/env python3
"""
Quick test to check imports without starting the full server.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_critical_imports():
    """Test the most critical imports that are causing server startup issues."""
    
    print("Testing critical imports...")
    
    # Test constants
    try:
        from constants import constant_common, constant_mt, constant_mocap
        print("✅ Constants import: OK")
    except Exception as e:
        print(f"❌ Constants import: FAILED - {e}")
        return False
    
    # Test utils.common
    try:
        from utils import common
        print("✅ Utils.common import: OK")
    except Exception as e:
        print(f"❌ Utils.common import: FAILED - {e}")
        return False
    
    # Test MT utils
    try:
        from utils.mt import preprocessing_mt, calibration_mt, ik_mt
        print("✅ MT utils import: OK")
    except Exception as e:
        print(f"❌ MT utils import: FAILED - {e}")
        return False
    
    # Test scripts
    try:
        from scripts.run_mt import mt_ik_in_memory
        print("✅ Scripts import: OK")
    except Exception as e:
        print(f"❌ Scripts import: FAILED - {e}")
        return False
    
    # Test new utils
    try:
        from utils.mot_generator import create_mot_file
        print("✅ MOT generator import: OK")
    except Exception as e:
        print(f"❌ MOT generator import: FAILED - {e}")
        return False
    
    try:
        from utils.osim2video_complete import generate_video_from_motion_complete
        print("✅ Video generator import: OK")
    except Exception as e:
        print(f"❌ Video generator import: FAILED - {e}")
        return False
    
    print("\n✅ All critical imports successful!")
    return True

if __name__ == "__main__":
    if test_critical_imports():
        print("\n🎉 Ready to start the server!")
        print("Run: python run.py")
    else:
        print("\n❌ Import issues need to be resolved first.") 
"""
Quick test to check imports without starting the full server.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_critical_imports():
    """Test the most critical imports that are causing server startup issues."""
    
    print("Testing critical imports...")
    
    # Test constants
    try:
        from constants import constant_common, constant_mt, constant_mocap
        print("✅ Constants import: OK")
    except Exception as e:
        print(f"❌ Constants import: FAILED - {e}")
        return False
    
    # Test utils.common
    try:
        from utils import common
        print("✅ Utils.common import: OK")
    except Exception as e:
        print(f"❌ Utils.common import: FAILED - {e}")
        return False
    
    # Test MT utils
    try:
        from utils.mt import preprocessing_mt, calibration_mt, ik_mt
        print("✅ MT utils import: OK")
    except Exception as e:
        print(f"❌ MT utils import: FAILED - {e}")
        return False
    
    # Test scripts
    try:
        from scripts.run_mt import mt_ik_in_memory
        print("✅ Scripts import: OK")
    except Exception as e:
        print(f"❌ Scripts import: FAILED - {e}")
        return False
    
    # Test new utils
    try:
        from utils.mot_generator import create_mot_file
        print("✅ MOT generator import: OK")
    except Exception as e:
        print(f"❌ MOT generator import: FAILED - {e}")
        return False
    
    try:
        from utils.osim2video_complete import generate_video_from_motion_complete
        print("✅ Video generator import: OK")
    except Exception as e:
        print(f"❌ Video generator import: FAILED - {e}")
        return False
    
    print("\n✅ All critical imports successful!")
    return True

if __name__ == "__main__":
    if test_critical_imports():
        print("\n🎉 Ready to start the server!")
        print("Run: python run.py")
    else:
        print("\n❌ Import issues need to be resolved first.") 
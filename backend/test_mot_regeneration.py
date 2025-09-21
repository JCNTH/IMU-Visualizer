#!/usr/bin/env python3
"""Test MOT file regeneration with complete joint angle data"""

import sys
import json
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.mot_generator import create_mot_file

def test_mot_regeneration():
    """Regenerate MOT file with complete data including pelvis position"""
    
    # Load the stored IK results
    results_path = Path("static/sessions/session_ik_results.json")
    
    if not results_path.exists():
        print(f"❌ No stored IK results found: {results_path}")
        return False
    
    print("🔍 Loading IK results and regenerating MOT file...")
    
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        joint_angles = results.get("joint_angles", {})
        
        print(f"📊 Original joint angles: {len(joint_angles)} columns")
        
        # Add missing pelvis position data with proper defaults
        n_frames = len(joint_angles['pelvis_tilt']) if 'pelvis_tilt' in joint_angles else 2243
        
        # Add pelvis position with defaults (critical for OpenSim positioning)
        if 'pelvis_tx' not in joint_angles:
            joint_angles['pelvis_tx'] = [0.0] * n_frames  # No forward/backward movement
            print("✅ Added pelvis_tx (forward/backward position)")
            
        if 'pelvis_ty' not in joint_angles:
            joint_angles['pelvis_ty'] = [0.9] * n_frames  # 0.9m height (standing)
            print("✅ Added pelvis_ty (height position)")
            
        if 'pelvis_tz' not in joint_angles:
            joint_angles['pelvis_tz'] = [0.0] * n_frames  # No left/right movement
            print("✅ Added pelvis_tz (left/right position)")
        
        print(f"📊 Enhanced joint angles: {len(joint_angles)} columns")
        
        # Regenerate MOT file with complete data
        output_path = "static/sessions/session_ik_COMPLETE.mot"
        
        print(f"🔨 Regenerating MOT file: {output_path}")
        mot_path = create_mot_file(joint_angles, output_path)
        
        if Path(mot_path).exists():
            file_size = Path(mot_path).stat().st_size / 1024  # KB
            print(f"✅ MOT file regenerated: {mot_path}")
            print(f"📦 Size: {file_size:.1f} KB")
            
            # Check the header to verify columns
            with open(mot_path, 'r') as f:
                lines = f.readlines()
            
            header_line = None
            for line in lines:
                if line.startswith('time\t'):
                    header_line = line.strip()
                    break
            
            if header_line:
                columns = header_line.split('\t')
                print(f"📋 MOT file columns ({len(columns)}):")
                for i, col in enumerate(columns):
                    print(f"   {i+1:2d}. {col}")
                
                # Check for critical pelvis columns
                critical_cols = ['pelvis_tilt', 'pelvis_list', 'pelvis_rot', 'pelvis_tx', 'pelvis_ty', 'pelvis_tz']
                missing_critical = [col for col in critical_cols if col not in columns]
                
                if missing_critical:
                    print(f"❌ Still missing critical columns: {missing_critical}")
                    return False
                else:
                    print(f"✅ All critical pelvis columns present!")
                    return True
            else:
                print("❌ Could not find header line in MOT file")
                return False
        else:
            print(f"❌ MOT file not created: {mot_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error regenerating MOT file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mot_regeneration()
    if success:
        print("\n🎉 MOT file regeneration SUCCESSFUL!")
        print("🎯 The complete MOT file should now work with OpenSim video generation")
        print("💡 Test with: python debug_single_frame.py")
    else:
        print("\n❌ MOT file regeneration FAILED!")
        print("🔧 Check the missing data and column mappings") 
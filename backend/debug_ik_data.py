#!/usr/bin/env python3
"""Debug script to see exactly what joint angle data the IK pipeline generates"""

import sys
import json
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

def debug_ik_data():
    """Load stored IK results and analyze the data structure"""
    
    # Check if we have stored IK results
    results_path = Path("static/sessions/session_ik_results.json")
    
    if not results_path.exists():
        print(f"❌ No stored IK results found: {results_path}")
        print("💡 Run IK processing first to generate data")
        return False
    
    print("🔍 Loading stored IK results...")
    
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        joint_angles = results.get("joint_angles", {})
        time_data = results.get("time", {})
        
        print(f"📊 IK Results Analysis:")
        print(f"   Session: {results.get('session_name', 'Unknown')}")
        print(f"   Joint angles keys: {len(joint_angles)}")
        print(f"   Time data keys: {len(time_data)}")
        
        if joint_angles:
            print(f"\n📋 Available Joint Angles:")
            for joint_name, angle_data in joint_angles.items():
                if isinstance(angle_data, list):
                    data_length = len(angle_data)
                    sample_values = angle_data[:3] if len(angle_data) >= 3 else angle_data
                    print(f"   ✅ {joint_name}: {data_length} frames, sample: {sample_values}")
                else:
                    print(f"   ❓ {joint_name}: {type(angle_data)} - {angle_data}")
        
        # Check what's missing for OpenSim
        required_for_opensim = [
            'pelvis_tilt', 'pelvis_list', 'pelvis_rot',
            'pelvis_tx', 'pelvis_ty', 'pelvis_tz',
            'hip_flexion_r', 'hip_adduction_r', 'hip_rotation_r',
            'knee_flexion_r', 'ankle_flexion_r',
            'hip_flexion_l', 'hip_adduction_l', 'hip_rotation_l', 
            'knee_flexion_l', 'ankle_flexion_l'
        ]
        
        print(f"\n🎯 OpenSim Requirements Check:")
        missing_data = []
        present_data = []
        
        for req_joint in required_for_opensim:
            if req_joint in joint_angles:
                present_data.append(req_joint)
                print(f"   ✅ {req_joint}")
            else:
                missing_data.append(req_joint)
                print(f"   ❌ {req_joint} - MISSING!")
        
        print(f"\n📊 Summary:")
        print(f"   Present: {len(present_data)}/{len(required_for_opensim)} ({100*len(present_data)/len(required_for_opensim):.1f}%)")
        print(f"   Missing: {len(missing_data)} critical joints")
        
        if missing_data:
            print(f"\n🔧 Missing joints that cause blank video:")
            for missing in missing_data:
                print(f"      - {missing}")
        
        # Check if pelvis data is there but with different names
        pelvis_variants = ['pelvis_tilt', 'pelvis_list', 'pelvis_rot', 'pelvis_rotation']
        print(f"\n🔍 Pelvis Data Search:")
        for variant in pelvis_variants:
            if variant in joint_angles:
                print(f"   ✅ Found: {variant}")
            else:
                print(f"   ❌ Missing: {variant}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading IK results: {e}")
        return False

if __name__ == "__main__":
    success = debug_ik_data()
    if success:
        print("\n✅ IK data analysis complete!")
        print("🎯 Use this info to fix the missing joint angle mappings")
    else:
        print("\n❌ Could not analyze IK data")
        print("🔧 Make sure to run IK processing first") 
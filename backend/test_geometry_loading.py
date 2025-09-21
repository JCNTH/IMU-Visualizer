#!/usr/bin/env python3
"""Test script to verify geometry loading with corrected paths"""

import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.osim2video_imu import get_vtp_mesh_arrays

def test_geometry_loading():
    """Test if we can load geometry files with the corrected paths"""
    
    print("🔍 Testing geometry loading with corrected paths...")
    
    # Check if Model directory exists
    model_dir = Path("Model")
    if not model_dir.exists():
        print(f"❌ Model directory not found: {model_dir}")
        return False
        
    geometry_dir = model_dir / "Geometry"
    if not geometry_dir.exists():
        print(f"❌ Geometry directory not found: {geometry_dir}")
        return False
        
    print(f"✅ Found Model directory: {model_dir}")
    print(f"✅ Found Geometry directory: {geometry_dir}")
    
    # Count geometry files
    vtp_files = list(geometry_dir.glob("*.vtp"))
    print(f"📁 Found {len(vtp_files)} .vtp geometry files")
    
    # Test loading the model file
    model_files = list(model_dir.glob("*.osim"))
    if not model_files:
        print("❌ No .osim model files found")
        return False
        
    model_file = model_dir / "LaiArnoldModified2017_poly_withArms_weldHand_scaled_adjusted.osim"
    if not model_file.exists():
        print(f"❌ Target model file not found: {model_file}")
        return False
        
    print(f"✅ Found working model file: {model_file}")
    
    # Parse the model to see what geometry it references
    try:
        print("🔍 Parsing model file to check geometry references...")
        tree = ET.parse(model_file)
        root = tree.getroot()
        
        bodySet = root.find("./Model/BodySet")
        if bodySet is None:
            print("❌ No BodySet found in model")
            return False
            
        body_count = 0
        geometry_refs = []
        
        for bodyElem in bodySet.findall("./objects/Body"):
            bname = bodyElem.get("name")
            body_count += 1
            
            # Check for attached geometry
            for meshElem in bodyElem.findall("./attached_geometry/Mesh"):
                meshFile = meshElem.find("mesh_file")
                if meshFile is not None:
                    mesh_path = meshFile.text.strip()
                    geometry_refs.append((bname, mesh_path))
        
        print(f"📋 Model contains {body_count} body segments")
        print(f"📋 Found {len(geometry_refs)} geometry references")
        
        # Test loading a few geometry files
        test_count = 0
        success_count = 0
        
        for body_name, mesh_rel_path in geometry_refs[:5]:  # Test first 5
            mesh_abs_path = geometry_dir / mesh_rel_path
            test_count += 1
            
            try:
                if mesh_abs_path.exists():
                    faceCounts, faceIndices, points = get_vtp_mesh_arrays(str(mesh_abs_path))
                    success_count += 1
                    print(f"✅ Loaded {mesh_rel_path}: {len(points)} vertices, {len(faceCounts)} faces")
                else:
                    print(f"❌ Geometry file not found: {mesh_abs_path}")
            except Exception as e:
                print(f"❌ Failed to load {mesh_rel_path}: {e}")
        
        print(f"📊 Geometry loading test: {success_count}/{test_count} successful")
        
        if success_count == test_count:
            print("🎉 All geometry files loaded successfully!")
            return True
        else:
            print(f"⚠️  Some geometry files failed to load")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing model file: {e}")
        return False

if __name__ == "__main__":
    success = test_geometry_loading()
    if success:
        print("\n✅ Geometry loading test PASSED!")
        print("🎯 The corrected paths should fix the blank video issue.")
        print("💡 Run debug_single_frame.py to test video generation.")
    else:
        print("\n❌ Geometry loading test FAILED!")
        print("🔧 Check the Model directory structure and file paths.") 
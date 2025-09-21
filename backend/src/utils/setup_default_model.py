#!/usr/bin/env python3
"""
Script to set up default OpenSim model for video generation.
Copies the essential model file from mbl_osim2obj to mbl_imuviz.
"""

import shutil
import os
from pathlib import Path

def setup_default_model():
    """Copy the default OpenSim model and geometry files."""
    
    # Paths
    backend_dir = Path(__file__).parent.parent.parent
    static_dir = backend_dir / "static" / "models"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Source paths (mbl_osim2obj) - check multiple possible locations
    possible_osim2obj_dirs = [
        Path(__file__).parent.parent.parent.parent.parent / "mbl_osim2obj",  # Same parent directory
        Path.home() / "Desktop" / "mbl_osim2obj",  # Desktop
        Path("/Users/julianng-thow-hing/Desktop/mbl_osim2obj"),  # Absolute path
    ]
    
    source_model = None
    source_geometry_dir = None
    
    for osim2obj_dir in possible_osim2obj_dirs:
        potential_model = osim2obj_dir / "Motions" / "imu" / "imu_scaled_model.osim"
        potential_geometry = osim2obj_dir / "Motions" / "imu" / "Geometry"
        if potential_model.exists():
            source_model = potential_model
            source_geometry_dir = potential_geometry
            print(f"Found mbl_osim2obj at: {osim2obj_dir}")
            break
    
    # Destination paths
    dest_model = static_dir / "default_model.osim"
    dest_geometry_dir = static_dir / "Geometry"
    
    try:
        # Copy model file
        if source_model and source_model.exists():
            shutil.copy2(source_model, dest_model)
            print(f"Copied model: {source_model} -> {dest_model}")
        else:
            print(f"Warning: Source model not found, creating minimal model")
            # Create a minimal placeholder model
            create_minimal_model(dest_model)
        
        # Copy geometry directory if it exists
        if source_geometry_dir and source_geometry_dir.exists():
            if dest_geometry_dir.exists():
                shutil.rmtree(dest_geometry_dir)
            shutil.copytree(source_geometry_dir, dest_geometry_dir)
            print(f"Copied geometry: {source_geometry_dir} -> {dest_geometry_dir}")
        else:
            print(f"Warning: Source geometry directory not found, creating empty directory")
            # Create empty geometry directory
            dest_geometry_dir.mkdir(exist_ok=True)
            print(f"Created empty geometry directory: {dest_geometry_dir}")
        
        print("Default model setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up default model: {e}")
        return False

def create_minimal_model(model_path: Path):
    """Create a minimal OpenSim model file as fallback."""
    
    minimal_model_content = """<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
    <Model name="MinimalModel">
        <defaults />
        <credits>Minimal model for IMU visualization</credits>
        <publications />
        <length_units>meters</length_units>
        <force_units>N</force_units>
        <BodySet name="bodyset">
            <objects>
                <Body name="ground">
                    <mass>0</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>0</inertia_xx>
                    <inertia_yy>0</inertia_yy>
                    <inertia_zz>0</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
                <Body name="pelvis">
                    <mass>1</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>1</inertia_xx>
                    <inertia_yy>1</inertia_yy>
                    <inertia_zz>1</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
                <Body name="femur_r">
                    <mass>1</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>1</inertia_xx>
                    <inertia_yy>1</inertia_yy>
                    <inertia_zz>1</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
                <Body name="tibia_r">
                    <mass>1</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>1</inertia_xx>
                    <inertia_yy>1</inertia_yy>
                    <inertia_zz>1</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
                <Body name="calcn_r">
                    <mass>1</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>1</inertia_xx>
                    <inertia_yy>1</inertia_yy>
                    <inertia_zz>1</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
                <Body name="femur_l">
                    <mass>1</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>1</inertia_xx>
                    <inertia_yy>1</inertia_yy>
                    <inertia_zz>1</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
                <Body name="tibia_l">
                    <mass>1</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>1</inertia_xx>
                    <inertia_yy>1</inertia_yy>
                    <inertia_zz>1</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
                <Body name="calcn_l">
                    <mass>1</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia_xx>1</inertia_xx>
                    <inertia_yy>1</inertia_yy>
                    <inertia_zz>1</inertia_zz>
                    <inertia_xy>0</inertia_xy>
                    <inertia_xz>0</inertia_xz>
                    <inertia_yz>0</inertia_yz>
                </Body>
            </objects>
            <groups />
        </BodySet>
        <JointSet name="jointset">
            <objects>
                <FreeJoint name="ground_pelvis">
                    <parent_body>ground</parent_body>
                    <child_body>pelvis</child_body>
                    <location_in_parent>0 0 0</location_in_parent>
                    <orientation_in_parent>0 0 0</orientation_in_parent>
                    <location>0 0 0</location>
                    <orientation>0 0 0</orientation>
                </FreeJoint>
                <CustomJoint name="hip_r">
                    <parent_body>pelvis</parent_body>
                    <child_body>femur_r</child_body>
                    <location_in_parent>0 0 0</location_in_parent>
                    <orientation_in_parent>0 0 0</orientation_in_parent>
                    <location>0 0 0</location>
                    <orientation>0 0 0</orientation>
                </CustomJoint>
                <CustomJoint name="knee_r">
                    <parent_body>femur_r</parent_body>
                    <child_body>tibia_r</child_body>
                    <location_in_parent>0 -0.4 0</location_in_parent>
                    <orientation_in_parent>0 0 0</orientation_in_parent>
                    <location>0 0 0</location>
                    <orientation>0 0 0</orientation>
                </CustomJoint>
                <CustomJoint name="ankle_r">
                    <parent_body>tibia_r</parent_body>
                    <child_body>calcn_r</child_body>
                    <location_in_parent>0 -0.4 0</location_in_parent>
                    <orientation_in_parent>0 0 0</orientation_in_parent>
                    <location>0 0 0</location>
                    <orientation>0 0 0</orientation>
                </CustomJoint>
                <CustomJoint name="hip_l">
                    <parent_body>pelvis</parent_body>
                    <child_body>femur_l</child_body>
                    <location_in_parent>0 0 0</location_in_parent>
                    <orientation_in_parent>0 0 0</orientation_in_parent>
                    <location>0 0 0</location>
                    <orientation>0 0 0</orientation>
                </CustomJoint>
                <CustomJoint name="knee_l">
                    <parent_body>femur_l</parent_body>
                    <child_body>tibia_l</child_body>
                    <location_in_parent>0 -0.4 0</location_in_parent>
                    <orientation_in_parent>0 0 0</orientation_in_parent>
                    <location>0 0 0</location>
                    <orientation>0 0 0</orientation>
                </CustomJoint>
                <CustomJoint name="ankle_l">
                    <parent_body>tibia_l</parent_body>
                    <child_body>calcn_l</child_body>
                    <location_in_parent>0 -0.4 0</location_in_parent>
                    <orientation_in_parent>0 0 0</orientation_in_parent>
                    <location>0 0 0</location>
                    <orientation>0 0 0</orientation>
                </CustomJoint>
            </objects>
            <groups />
        </JointSet>
        <CoordinateSet name="coordinateset">
            <objects />
            <groups />
        </CoordinateSet>
    </Model>
</OpenSimDocument>"""
    
    with open(model_path, 'w') as f:
        f.write(minimal_model_content)
    
    print(f"Created minimal model: {model_path}")

if __name__ == "__main__":
    setup_default_model() 
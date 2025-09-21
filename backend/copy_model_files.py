#!/usr/bin/env python3
"""
Script to copy essential model files from mbl_osim2obj to mbl_imuviz.
"""

import shutil
import os
from pathlib import Path

def copy_model_files():
    """Copy essential model files from mbl_osim2obj."""
    
    # Source directory (mbl_osim2obj)
    osim2obj_dir = Path("/Users/julianng-thow-hing/Desktop/mbl_osim2obj")
    
    # Destination directory (mbl_imuviz)
    backend_dir = Path(__file__).parent
    static_dir = backend_dir / "static"
    models_dir = static_dir / "models"
    
    # Create directories
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("Copying essential files from mbl_osim2obj...")
    print("=" * 50)
    
    # Files to copy
    files_to_copy = [
        {
            "src": osim2obj_dir / "Motions" / "imu" / "imu_scaled_model.osim",
            "dst": models_dir / "imu_scaled_model.osim"
        },
        {
            "src": osim2obj_dir / "Model" / "LaiArnoldModified2017_poly_withArms_weldHand_scaled_adjusted.osim", 
            "dst": models_dir / "default_model.osim"
        },
        {
            "src": osim2obj_dir / "Camera" / "calib.npz",
            "dst": models_dir / "default_calib.npz"
        },
        {
            "src": osim2obj_dir / "mot2quats.py",
            "dst": backend_dir / "src" / "utils" / "mot2quats_original.py"  # Keep as reference
        }
    ]
    
    # Directories to copy
    dirs_to_copy = [
        {
            "src": osim2obj_dir / "Motions" / "imu" / "Geometry",
            "dst": models_dir / "imu_geometry"
        },
        {
            "src": osim2obj_dir / "Model" / "Geometry", 
            "dst": models_dir / "Geometry"
        }
    ]
    
    # Copy files
    for file_info in files_to_copy:
        src = file_info["src"]
        dst = file_info["dst"]
        
        if src.exists():
            try:
                # Create destination directory if needed
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(src, dst)
                size_mb = dst.stat().st_size / (1024 * 1024)
                print(f"✅ Copied {src.name} -> {dst.name} ({size_mb:.1f} MB)")
            except Exception as e:
                print(f"❌ Failed to copy {src.name}: {e}")
        else:
            print(f"⚠️  Source file not found: {src}")
    
    # Copy directories
    for dir_info in dirs_to_copy:
        src = dir_info["src"]
        dst = dir_info["dst"]
        
        if src.exists():
            try:
                # Remove destination if it exists
                if dst.exists():
                    shutil.rmtree(dst)
                
                shutil.copytree(src, dst)
                file_count = len(list(dst.rglob("*")))
                print(f"✅ Copied directory {src.name} -> {dst.name} ({file_count} files)")
            except Exception as e:
                print(f"❌ Failed to copy directory {src.name}: {e}")
        else:
            print(f"⚠️  Source directory not found: {src}")
    
    print("\n" + "=" * 50)
    print("Model files copied successfully!")
    print("=" * 50)
    
    # List what was copied
    print("\nFiles now available in mbl_imuviz:")
    for item in models_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(models_dir)
            size_mb = item.stat().st_size / (1024 * 1024)
            print(f"📁 {rel_path} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    copy_model_files() 
"""
Script to copy essential model files from mbl_osim2obj to mbl_imuviz.
"""

import shutil
import os
from pathlib import Path

def copy_model_files():
    """Copy essential model files from mbl_osim2obj."""
    
    # Source directory (mbl_osim2obj)
    osim2obj_dir = Path("/Users/julianng-thow-hing/Desktop/mbl_osim2obj")
    
    # Destination directory (mbl_imuviz)
    backend_dir = Path(__file__).parent
    static_dir = backend_dir / "static"
    models_dir = static_dir / "models"
    
    # Create directories
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("Copying essential files from mbl_osim2obj...")
    print("=" * 50)
    
    # Files to copy
    files_to_copy = [
        {
            "src": osim2obj_dir / "Motions" / "imu" / "imu_scaled_model.osim",
            "dst": models_dir / "imu_scaled_model.osim"
        },
        {
            "src": osim2obj_dir / "Model" / "LaiArnoldModified2017_poly_withArms_weldHand_scaled_adjusted.osim", 
            "dst": models_dir / "default_model.osim"
        },
        {
            "src": osim2obj_dir / "Camera" / "calib.npz",
            "dst": models_dir / "default_calib.npz"
        },
        {
            "src": osim2obj_dir / "mot2quats.py",
            "dst": backend_dir / "src" / "utils" / "mot2quats_original.py"  # Keep as reference
        }
    ]
    
    # Directories to copy
    dirs_to_copy = [
        {
            "src": osim2obj_dir / "Motions" / "imu" / "Geometry",
            "dst": models_dir / "imu_geometry"
        },
        {
            "src": osim2obj_dir / "Model" / "Geometry", 
            "dst": models_dir / "Geometry"
        }
    ]
    
    # Copy files
    for file_info in files_to_copy:
        src = file_info["src"]
        dst = file_info["dst"]
        
        if src.exists():
            try:
                # Create destination directory if needed
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(src, dst)
                size_mb = dst.stat().st_size / (1024 * 1024)
                print(f"✅ Copied {src.name} -> {dst.name} ({size_mb:.1f} MB)")
            except Exception as e:
                print(f"❌ Failed to copy {src.name}: {e}")
        else:
            print(f"⚠️  Source file not found: {src}")
    
    # Copy directories
    for dir_info in dirs_to_copy:
        src = dir_info["src"]
        dst = dir_info["dst"]
        
        if src.exists():
            try:
                # Remove destination if it exists
                if dst.exists():
                    shutil.rmtree(dst)
                
                shutil.copytree(src, dst)
                file_count = len(list(dst.rglob("*")))
                print(f"✅ Copied directory {src.name} -> {dst.name} ({file_count} files)")
            except Exception as e:
                print(f"❌ Failed to copy directory {src.name}: {e}")
        else:
            print(f"⚠️  Source directory not found: {src}")
    
    print("\n" + "=" * 50)
    print("Model files copied successfully!")
    print("=" * 50)
    
    # List what was copied
    print("\nFiles now available in mbl_imuviz:")
    for item in models_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(models_dir)
            size_mb = item.stat().st_size / (1024 * 1024)
            print(f"📁 {rel_path} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    copy_model_files() 
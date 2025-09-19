#!/usr/bin/env python3
"""
Script to create a default camera calibration file for video generation.
"""

import numpy as np
import os
from pathlib import Path

def create_default_calibration(output_path: str):
    """Create a default camera calibration file."""
    
    # Default camera intrinsics (640x480 resolution)
    K = np.array([
        [800.0, 0.0, 320.0],
        [0.0, 800.0, 240.0], 
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)
    
    # Identity rotation (camera aligned with world)
    R = np.eye(3, dtype=np.float64)
    
    # Camera positioned 3 meters back from origin, 1 meter up
    T = np.array([0.0, 1.0, -3.0], dtype=np.float64)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save calibration
    np.savez(output_path, K=K, R=R, T=T)
    
    print(f"Created default camera calibration: {output_path}")
    print(f"Camera intrinsics K:\n{K}")
    print(f"Camera rotation R:\n{R}")
    print(f"Camera translation T: {T}")

if __name__ == "__main__":
    # Get the backend static directory
    backend_dir = Path(__file__).parent.parent.parent
    static_dir = backend_dir / "static" / "models"
    
    calib_path = static_dir / "default_calib.npz"
    create_default_calibration(str(calib_path)) 
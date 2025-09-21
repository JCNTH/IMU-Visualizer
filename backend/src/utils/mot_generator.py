"""
mot_generator.py

Utility to convert joint angles dictionary to OpenSim .mot file format.
This replaces the DataFrame output from IK service to enable video generation.
"""

import os
import numpy as np
from typing import Dict, Any, List
from pathlib import Path

def create_mot_file(joint_angles: Dict[str, Any], output_path: str, time_step: float = 0.01) -> str:
    """
    Convert joint angles dictionary to OpenSim .mot file format.
    
    Args:
        joint_angles: Dictionary with joint names as keys and angle arrays as values
        output_path: Path to save the .mot file
        time_step: Time step between frames (default 0.01s = 100Hz)
    
    Returns:
        Path to the created .mot file
    """
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get the number of frames from the first joint
    first_joint = next(iter(joint_angles.values()))
    n_frames = len(first_joint)
    
    # Create time array
    times = np.arange(0, n_frames * time_step, time_step)[:n_frames]
    
    # Define the standard joint order for OpenSim
    # This matches the expected coordinate names in the OpenSim model
    joint_order = [
        'pelvis_tilt', 'pelvis_list', 'pelvis_rot',  # Use 'pelvis_rot' to match ik_mt.py output
        'pelvis_tx', 'pelvis_ty', 'pelvis_tz',
        'hip_flexion_r', 'hip_adduction_r', 'hip_rotation_r',
        'knee_adduction_r', 'knee_rotation_r', 'knee_flexion_r',  # Include all knee DOFs
        'ankle_adduction_r', 'ankle_rotation_r', 'ankle_flexion_r',  # Use ankle_flexion to match ik_mt.py
        'hip_flexion_l', 'hip_adduction_l', 'hip_rotation_l',
        'knee_adduction_l', 'knee_rotation_l', 'knee_flexion_l',  # Include all knee DOFs
        'ankle_adduction_l', 'ankle_rotation_l', 'ankle_flexion_l',  # Use ankle_flexion to match ik_mt.py
        'lumbar_extension', 'lumbar_bending', 'lumbar_rotation'
    ]
    
    # Create mapping for column name compatibility
    column_mapping = {
        'pelvis_rotation': 'pelvis_rot',  # Map OpenSim name to IK pipeline name
        'ankle_angle_l': 'ankle_flexion_l',
        'ankle_angle_r': 'ankle_flexion_r',
        'knee_angle_l': 'knee_flexion_l', 
        'knee_angle_r': 'knee_flexion_r'
    }
    
    print(f"DEBUG: Available joint angles: {list(joint_angles.keys())}")
    
    # Map the input joint angles to the standard order
    # Fill missing joints with zeros
    ordered_data = {}
    for joint_name in joint_order:
        # Check direct name first, then mapped name
        actual_key = joint_name
        if joint_name not in joint_angles and joint_name in column_mapping:
            actual_key = column_mapping[joint_name]
        
        if actual_key in joint_angles:
            # Convert from radians to degrees (OpenSim expects degrees)
            if 'tx' not in joint_name and 'ty' not in joint_name and 'tz' not in joint_name:
                ordered_data[joint_name] = np.rad2deg(joint_angles[actual_key])
                print(f"DEBUG: Mapped {joint_name} -> {actual_key}")
            else:
                # Translation coordinates (keep in meters)
                ordered_data[joint_name] = joint_angles.get(actual_key, np.zeros(n_frames))
        else:
            # Fill missing joints with zeros
            print(f"WARNING: Missing joint angle data for '{joint_name}' (also tried '{column_mapping.get(joint_name, 'N/A')}'), filling with zeros")
            ordered_data[joint_name] = np.zeros(n_frames)
    
    # Add pelvis translations if not present (set to reasonable defaults)
    if 'pelvis_tx' not in joint_angles:
        ordered_data['pelvis_tx'] = np.zeros(n_frames)
    if 'pelvis_ty' not in joint_angles:
        ordered_data['pelvis_ty'] = np.ones(n_frames) * 0.9  # 0.9m height
    if 'pelvis_tz' not in joint_angles:
        ordered_data['pelvis_tz'] = np.zeros(n_frames)
    
    # Write the .mot file
    with open(output_path, 'w') as f:
        # Write header
        f.write("Coordinates\n")
        f.write("version=1\n")
        f.write(f"nRows={n_frames}\n")
        f.write(f"nColumns={len(joint_order) + 1}\n")  # +1 for time column
        f.write("inDegrees=yes\n")
        f.write("\n")
        f.write("Units are S.I. units (second, meters, Newtons, ...)\n")
        f.write("If the header above contains a line with 'inDegrees', this indicates whether rotational values are in degrees (yes) or radians (no).\n")
        f.write("\n")
        f.write("endheader\n")
        
        # Write column headers
        headers = ['time'] + joint_order
        f.write('\t'.join(headers) + '\n')
        
        # Write data
        for i in range(n_frames):
            row = [f"{times[i]:.5f}"]
            for joint_name in joint_order:
                row.append(f"{ordered_data[joint_name][i]:.6f}")
            f.write('\t'.join(row) + '\n')
    
    print(f"Created .mot file with {n_frames} frames: {output_path}")
    return output_path

def create_mot_from_ik_results(ik_results: Dict[str, Any], output_dir: str, session_name: str = "session") -> str:
    """
    Create a .mot file from IK service results.
    
    Args:
        ik_results: Results from the IK service containing joint_angles
        output_dir: Directory to save the .mot file
        session_name: Name for the session (used in filename)
    
    Returns:
        Path to the created .mot file
    """
    
    if 'joint_angles' not in ik_results:
        raise ValueError("IK results must contain 'joint_angles' key")
    
    joint_angles = ik_results['joint_angles']
    
    # Create output filename
    mot_filename = f"{session_name}_ik.mot"
    mot_path = os.path.join(output_dir, mot_filename)
    
    return create_mot_file(joint_angles, mot_path)

def validate_mot_file(mot_path: str) -> bool:
    """
    Validate that a .mot file is properly formatted.
    
    Args:
        mot_path: Path to the .mot file
    
    Returns:
        True if valid, False otherwise
    """
    
    try:
        with open(mot_path, 'r') as f:
            lines = f.readlines()
        
        # Check for required header elements
        header_found = False
        endheader_found = False
        
        for line in lines:
            line = line.strip()
            if line == "endheader":
                endheader_found = True
                break
            if line.startswith("version="):
                header_found = True
        
        if not header_found or not endheader_found:
            return False
        
        # Check that there's data after the header
        data_lines = [line for line in lines if not line.strip().startswith(('Coordinates', 'version=', 'nRows=', 'nColumns=', 'inDegrees=', 'Units', 'If the header', 'endheader', '')) and line.strip()]
        
        if len(data_lines) < 2:  # At least header and one data row
            return False
        
        return True
        
    except Exception as e:
        print(f"Error validating .mot file: {e}")
        return False

def get_mot_info(mot_path: str) -> Dict[str, Any]:
    """
    Get information about a .mot file.
    
    Args:
        mot_path: Path to the .mot file
    
    Returns:
        Dictionary with file information
    """
    
    info = {
        'valid': False,
        'n_rows': 0,
        'n_columns': 0,
        'in_degrees': False,
        'joints': [],
        'duration': 0.0,
        'sample_rate': 0.0
    }
    
    try:
        with open(mot_path, 'r') as f:
            lines = f.readlines()
        
        # Parse header
        for line in lines:
            line = line.strip()
            if line.startswith("nRows="):
                info['n_rows'] = int(line.split('=')[1])
            elif line.startswith("nColumns="):
                info['n_columns'] = int(line.split('=')[1])
            elif line.startswith("inDegrees="):
                info['in_degrees'] = line.split('=')[1].lower() == 'yes'
            elif line == "endheader":
                break
        
        # Find data section
        data_start = -1
        for i, line in enumerate(lines):
            if line.strip() == "endheader":
                data_start = i + 1
                break
        
        if data_start >= 0 and data_start < len(lines):
            # Get joint names from header row
            header_line = lines[data_start].strip()
            info['joints'] = header_line.split('\t')[1:]  # Skip time column
            
            # Get time information from first and last data rows
            if data_start + 1 < len(lines):
                first_data = lines[data_start + 1].strip().split('\t')
                last_data = lines[-1].strip().split('\t')
                
                if len(first_data) > 0 and len(last_data) > 0:
                    start_time = float(first_data[0])
                    end_time = float(last_data[0])
                    info['duration'] = end_time - start_time
                    
                    if info['n_rows'] > 1:
                        info['sample_rate'] = (info['n_rows'] - 1) / info['duration']
        
        info['valid'] = validate_mot_file(mot_path)
        
    except Exception as e:
        print(f"Error reading .mot file info: {e}")
    
    return info 
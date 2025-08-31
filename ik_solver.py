# ik_solver.py
import numpy as np
import pandas as pd
import json
import os
import sys
import traceback
import tempfile
import pickle
from pathlib import Path
from io import StringIO

# Import the in-memory MT IK pipeline
from scripts import run_mt  # Use the in-memory pipeline
from scripts.run_mt import mt_ik_in_memory

def convert_data_to_dataframe(data):
    try:
        print(f"DEBUG: Converting data of type: {type(data)}")
        if isinstance(data, pd.DataFrame):
            return data
        if isinstance(data, list):
            if len(data) == 0:
                raise ValueError("Empty data list")
            # Check if the first row (header) is smaller than the second row.
            if len(data[0]) < len(data[1]):
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                df = pd.DataFrame(data, columns=[f'col_{i}' for i in range(len(data[0]))])
            return df
        if isinstance(data, dict):
            if 'content' in data:
                data = data['content']
            df = pd.DataFrame.from_dict(data)
            print(f"DEBUG: Converted dict to DataFrame with shape {df.shape}")
            return df
        if isinstance(data, str):
            try:
                df = pd.read_csv(StringIO(data), sep='\t', comment='//')
                print(f"DEBUG: Converted string (tab-delimited) to DataFrame with shape {df.shape}")
                return df
            except Exception as ex:
                df = pd.read_csv(StringIO(data), sep=',')
                print(f"DEBUG: Converted string (comma-delimited) to DataFrame with shape {df.shape}")
                return df
        raise ValueError(f"Unsupported data type: {type(data)}")
    except Exception as e:
        print(f"Error converting data to DataFrame: {str(e)}")
        traceback.print_exc()
        raise

def run_ik(main_task_data, calibration_data, params=None):
    try:
        # Set default parameters if not provided.
        if params is None:
            params = {
                "subject": 1,
                "task": "treadmill_walking",
                "selected_setup": "mm",
                "filter_type": "Xsens",
                "dim": "9D",
                "remove_offset": True
            }
        print("DEBUG: Running IK with parameters:")
        # print(json.dumps(params, indent=2))
        
        # Print a short summary of main_task_data keys and (if possible) shapes.
        print("DEBUG: Main task data keys received:", list(main_task_data.keys()))
        for sensor, data in main_task_data.items():
            try:
                df = convert_data_to_dataframe(data)
                print(f"DEBUG: Sensor '{sensor}' main task data shape: {df.shape}")
            except Exception:
                print(f"ERROR: Could not convert main task data for sensor {sensor}")
        
        # Likewise, log the calibration data keys:
        print("DEBUG: Calibration data keys received:", list(calibration_data.keys()))
        for task_id, task_data in calibration_data.items():
            for sensor, data in task_data.items():
                try:
                    df = convert_data_to_dataframe(data)
                    print(f"DEBUG: Calibration data for task '{task_id}', sensor '{sensor}' shape: {df.shape}")
                except Exception:
                    print(f"ERROR: Could not convert calibration data for task '{task_id}', sensor '{sensor}'")
        
        # Call the in-memory IK pipeline.
        print("DEBUG: Calling mt_ik_in_memory with the provided data ...")
        results = mt_ik_in_memory(
            selected_setup=params.get("selected_setup", "mm"),
            f_type=params.get("filter_type", "Xsens"),
            dim=params.get("dim", "9D"),
            subject=params.get("subject", 1),
            task=params.get("task", "treadmill_walking"),
            remove_offset=params.get("remove_offset", True),
            calibration_data=calibration_data,
            main_task_data=main_task_data
        )
        
        print("DEBUG: IK pipeline returned the following results:")
        print(results)
        
        # Check if the computed joint angles are all zero.
        joint_angles = results.get("joint_angles")
        if joint_angles:
            all_zeros = True
            for joint, angles in joint_angles.items():
                arr = np.array(angles)
                if not np.allclose(arr, 0):
                    all_zeros = False
                    break
            if all_zeros:
                print("WARNING: All computed joint angles are zero. Verify sensor preprocessing and calibration!")
        else:
            print("DEBUG: No 'joint_angles' key found in results.")
        
        return results

    except Exception as e:
        print("ERROR: Exception encountered in run_ik:")
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == '__main__':
    # Dummy main task data with non-zero values.
    
    sample_main_task = {
        "foot_r": pd.DataFrame({
            "Acc_X": [5.0, 5.1, 5.2, 5.3, 5.4],
            "Acc_Y": [1.0, 1.1, 1.2, 1.3, 1.4],
            "Acc_Z": [7.9, 7.95, 8.0, 8.05, 8.1],
            "Gyr_X": [0.003, 0.004, 0.005, 0.006, 0.007],
            "Gyr_Y": [-0.001, -0.002, -0.003, -0.004, -0.005],
            "Gyr_Z": [0.001, 0.002, 0.003, 0.004, 0.005],
            "Mag_X": [-0.57, -0.58, -0.59, -0.60, -0.61],
            "Mag_Y": [0.53, 0.54, 0.55, 0.56, 0.57],
            "Mag_Z": [-0.41, -0.42, -0.43, -0.44, -0.45],
            "Quat_q0": [0.5, 0.51, 0.52, 0.53, 0.54],
            "Quat_q1": [-0.2, -0.21, -0.22, -0.23, -0.24],
            "Quat_q2": [-0.8, -0.81, -0.82, -0.83, -0.84],
            "Quat_q3": [0.3, 0.31, 0.32, 0.33, 0.34]
        })
    }
    
    # Dummy calibration data (ensure values are non-zero)
    sample_calibration = {
        "static": {
            "foot_r": pd.DataFrame({
                "Acc_X": [5.45, 5.46, 5.47, 5.48, 5.49],
                "Acc_Y": [1.40, 1.41, 1.42, 1.43, 1.44],
                "Acc_Z": [7.95, 7.96, 7.97, 7.98, 7.99],
                "Gyr_X": [0.002, 0.003, 0.004, 0.005, 0.006],
                "Gyr_Y": [-0.001, -0.0015, -0.002, -0.0025, -0.003],
                "Gyr_Z": [0.001, 0.0015, 0.002, 0.0025, 0.003],
                "Mag_X": [-0.57, -0.58, -0.59, -0.60, -0.61],
                "Mag_Y": [0.53, 0.54, 0.55, 0.56, 0.57],
                "Mag_Z": [-0.41, -0.42, -0.43, -0.44, -0.45],
                "Quat_q0": [0.51, 0.52, 0.53, 0.54, 0.55],
                "Quat_q1": [-0.21, -0.22, -0.23, -0.24, -0.25],
                "Quat_q2": [-0.81, -0.82, -0.83, -0.84, -0.85],
                "Quat_q3": [0.31, 0.32, 0.33, 0.34, 0.35]
            })
        },
        # You can add additional calibration tasks here if needed.
    }
    sample_params = {
        "subject": 1,
        "task": "treadmill_walking",
        "selected_setup": "mm",
        "filter_type": "Xsens",
        "dim": "9D",
        "remove_offset": True
    }
    
    test_results = run_ik(sample_main_task, sample_calibration, sample_params)
    print("Test IK Results:")
    print(test_results)

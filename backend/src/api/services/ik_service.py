import numpy as np
import pandas as pd
import traceback
import tempfile
import zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
from typing import Dict, Any, Optional
from pathlib import Path

# Import the existing MT IK pipeline
import sys
sys.path.append(str(Path(__file__).parent.parent))
from scripts.run_mt import mt_ik_in_memory

class IKService:
    """Service for handling inverse kinematics processing"""
    
    def convert_data_to_dataframe(self, data: Any) -> pd.DataFrame:
        """Convert various data formats to DataFrame"""
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
                except Exception:
                    df = pd.read_csv(StringIO(data), sep=',')
                    print(f"DEBUG: Converted string (comma-delimited) to DataFrame with shape {df.shape}")
                    return df
            raise ValueError(f"Unsupported data type: {type(data)}")
        except Exception as e:
            print(f"Error converting data to DataFrame: {str(e)}")
            traceback.print_exc()
            raise
    
    async def run_ik(self, main_task_data: Dict[str, Any], calibration_data: Dict[str, Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """Run inverse kinematics calculation"""
        try:
            print("DEBUG: Running IK with parameters:")
            
            # Print summary of main_task_data keys and shapes
            print("DEBUG: Main task data keys received:", list(main_task_data.keys()))
            for sensor, data in main_task_data.items():
                try:
                    df = self.convert_data_to_dataframe(data)
                    print(f"DEBUG: Sensor '{sensor}' main task data shape: {df.shape}")
                except Exception:
                    print(f"ERROR: Could not convert main task data for sensor {sensor}")
            
            # Log calibration data keys
            print("DEBUG: Calibration data keys received:", list(calibration_data.keys()))
            for task_id, task_data in calibration_data.items():
                for sensor, data in task_data.items():
                    try:
                        df = self.convert_data_to_dataframe(data)
                        print(f"DEBUG: Calibration data for task '{task_id}', sensor '{sensor}' shape: {df.shape}")
                    except Exception:
                        print(f"ERROR: Could not convert calibration data for task '{task_id}', sensor '{sensor}'")
            
            # Call the in-memory IK pipeline
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
            
            # Check if the computed joint angles are all zero
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
    
    def save_computed_joint_angles_to_dataframe(self, joint_angles: Dict[str, Any]) -> pd.DataFrame:
        """Convert joint angles dictionary to DataFrame with degrees to radians conversion"""
        # Define the desired order for left and right side keys
        order_left = ['hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_flexion_l', 'ankle_angle_l']
        order_right = ['hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_flexion_r', 'ankle_angle_r']
        
        # Create the list of keys to output – only add keys that exist in the IK dictionary
        column_order = [key for key in order_left if key in joint_angles] + \
                      [key for key in order_right if key in joint_angles]
        
        # Build a new dictionary with only those keys, converting values from degrees to radians
        data = {}
        for key in column_order:
            # Convert the value to a numpy array if it isn't already one,
            # then apply the deg2rad conversion
            arr = np.array(joint_angles[key])
            data[key] = np.deg2rad(arr)  # Converts every element from degrees to radians
        
        df = pd.DataFrame(data)
        return df[column_order]
    
    async def create_graphs_zip(self, joint_angles: Dict[str, Any]) -> bytes:
        """Create a ZIP file containing graphs for each joint angle"""
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Create a plot for each joint angle and write to the zip
            for angle_name, angle_data in joint_angles.items():
                plt.figure()
                plt.plot(angle_data)
                plt.title(angle_name)
                plt.xlabel("Sample Index")
                plt.ylabel("Angle")
                
                buf = BytesIO()
                plt.savefig(buf, format='png')
                plt.close()
                buf.seek(0)
                # Save the PNG file into the ZIP archive
                zipf.writestr(f"{angle_name}.png", buf.getvalue())
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue() 
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
from scripts.run_mt import mt_ik_in_memory

# Import the new mot generation utilities
from utils.mot_generator import create_mot_from_ik_results

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
    
    async def run_ik(self, main_task_data: Dict[str, Any], calibration_data: Dict[str, Dict[str, Any]], sensor_mapping: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
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
            
            # Apply sensor mapping to convert sensor IDs to body segment names
            print("DEBUG: Applying sensor mapping...")
            print("DEBUG: Sensor mapping:", sensor_mapping)
            
            # Track unmapped sensors for user feedback
            unmapped_sensors = []
            
            # Convert main task data using sensor mapping
            mapped_main_task_data = {}
            for sensor_key, sensor_data in main_task_data.items():
                # Extract sensor ID from the key (remove folder prefix if present)
                sensor_id = sensor_key.split('/')[-1].replace('.txt', '').replace('.csv', '')
                # Find the last part that looks like a sensor ID (8 hex characters)
                parts = sensor_id.split('_')
                actual_sensor_id = None
                for part in parts:
                    if len(part) == 8 and all(c in '0123456789ABCDEFabcdef' for c in part):
                        actual_sensor_id = part.upper()
                        break
                
                if actual_sensor_id and actual_sensor_id in sensor_mapping:
                    body_segment = sensor_mapping[actual_sensor_id]
                    mapped_main_task_data[body_segment] = sensor_data
                    print(f"DEBUG: Mapped sensor {actual_sensor_id} → {body_segment}")
                else:
                    unmapped_sensors.append({"file": sensor_key, "sensor_id": actual_sensor_id})
                    print(f"INFO: Skipping unmapped sensor {sensor_key} (ID: {actual_sensor_id}) - no mapping provided")
            
            # Convert calibration data using sensor mapping
            mapped_calibration_data = {}
            for task_id, task_data in calibration_data.items():
                mapped_calibration_data[task_id] = {}
                for sensor_key, sensor_data in task_data.items():
                    # Extract sensor ID from the key
                    sensor_id = sensor_key.split('/')[-1].replace('.txt', '').replace('.csv', '')
                    parts = sensor_id.split('_')
                    actual_sensor_id = None
                    for part in parts:
                        if len(part) == 8 and all(c in '0123456789ABCDEFabcdef' for c in part):
                            actual_sensor_id = part.upper()
                            break
                    
                    if actual_sensor_id and actual_sensor_id in sensor_mapping:
                        body_segment = sensor_mapping[actual_sensor_id]
                        mapped_calibration_data[task_id][body_segment] = sensor_data
                        print(f"DEBUG: Mapped calibration sensor {actual_sensor_id} → {body_segment}")
                    else:
                        print(f"INFO: Skipping unmapped calibration sensor {sensor_key} (ID: {actual_sensor_id}) - no mapping provided")
            
            # Summary of processing results
            total_main_files = len(main_task_data)
            mapped_main_files = len(mapped_main_task_data)
            total_calib_files = sum(len(task_data) for task_data in calibration_data.values())
            mapped_calib_files = sum(len(task_data) for task_data in mapped_calibration_data.values())
            
            print(f"INFO: Processing Summary:")
            print(f"  - Main task: {mapped_main_files}/{total_main_files} files mapped")
            print(f"  - Calibration: {mapped_calib_files}/{total_calib_files} files mapped")
            print(f"  - Unmapped sensors: {len(unmapped_sensors)} files skipped")
            
            print("DEBUG: Mapped main task data keys:", list(mapped_main_task_data.keys()))
            print("DEBUG: Mapped calibration data keys:", {k: list(v.keys()) for k, v in mapped_calibration_data.items()})
            
            # Check if we have minimum required sensors
            required_sensors = ['pelvis', 'thigh_l', 'shank_l', 'foot_l']
            missing_required = [sensor for sensor in required_sensors if sensor not in mapped_main_task_data]
            
            if missing_required:
                error_msg = f"Missing required sensors: {missing_required}. Please update your sensor mapping to include these body segments."
                print(f"ERROR: {error_msg}")
                return {"error": error_msg, "unmapped_sensors": unmapped_sensors}
            
            # Call the in-memory IK pipeline
            print("DEBUG: Calling mt_ik_in_memory with the mapped data ...")
            results = mt_ik_in_memory(
                selected_setup=params.get("selected_setup", "mm"),
                f_type=params.get("filter_type", "Xsens"),
                dim=params.get("dim", "9D"),
                subject=params.get("subject", 1),
                task=params.get("task", "treadmill_walking"),
                remove_offset=params.get("remove_offset", True),
                calibration_data=mapped_calibration_data,
                main_task_data=mapped_main_task_data
            )
            
            print("DEBUG: IK pipeline returned results")
            joint_angles = results.get("joint_angles", {})
            print(f"DEBUG: Available joint angles: {list(joint_angles.keys())}")
            
            # Add missing pelvis position data for OpenSim (critical!)
            if joint_angles and 'pelvis_tilt' in joint_angles:
                n_frames = len(joint_angles['pelvis_tilt'])
                
                if 'pelvis_tx' not in joint_angles:
                    joint_angles['pelvis_tx'] = np.zeros(n_frames)
                    print("DEBUG: Added pelvis_tx (forward/backward position)")
                    
                if 'pelvis_ty' not in joint_angles:
                    joint_angles['pelvis_ty'] = np.ones(n_frames) * 0.9  # 0.9m height
                    print("DEBUG: Added pelvis_ty (height position)")
                    
                if 'pelvis_tz' not in joint_angles:
                    joint_angles['pelvis_tz'] = np.zeros(n_frames)
                    print("DEBUG: Added pelvis_tz (left/right position)")
                
                # Update results with enhanced joint angles
                results["joint_angles"] = joint_angles
                print(f"DEBUG: Enhanced joint angles now has {len(joint_angles)} columns")
            
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
            
            # Add unmapped sensor information to successful results
            if "error" not in results and unmapped_sensors:
                results["unmapped_sensors"] = unmapped_sensors
            
            return results

        except Exception as e:
            print("ERROR: Exception encountered in run_ik:")
            traceback.print_exc()
            return {"error": str(e)}
    
    def save_computed_joint_angles_to_dataframe(self, joint_angles: Dict[str, Any]) -> pd.DataFrame:
        """Convert joint angles dictionary to DataFrame with degrees to radians conversion"""
        # Define the complete joint order including pelvis data (CRITICAL for OpenSim)
        pelvis_order = ['pelvis_tilt', 'pelvis_list', 'pelvis_rot']
        order_left = ['hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_adduction_l', 'knee_rotation_l', 'knee_flexion_l', 'ankle_adduction_l', 'ankle_rotation_l', 'ankle_flexion_l']
        order_right = ['hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_adduction_r', 'knee_rotation_r', 'knee_flexion_r', 'ankle_adduction_r', 'ankle_rotation_r', 'ankle_flexion_r']
        
        # Create the complete list of keys to output – include pelvis data!
        column_order = [key for key in pelvis_order if key in joint_angles] + \
                      [key for key in order_left if key in joint_angles] + \
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
    
    def create_mot_file(self, ik_results: Dict[str, Any], session_name: str = "session") -> str:
        """Create a .mot file from IK results for video generation"""
        try:
            # Create output directory in static folder
            static_dir = Path(__file__).parent.parent.parent.parent / "static" / "sessions"
            static_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate .mot file
            mot_path = create_mot_from_ik_results(ik_results, str(static_dir), session_name)
            
            print(f"Created .mot file: {mot_path}")
            return mot_path
            
        except Exception as e:
            print(f"Error creating .mot file: {e}")
            traceback.print_exc()
            raise 
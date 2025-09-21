# name: run_mt.py
# description: run unconstrained IK on MTw data
# author: Vu Phan
# date: 2024/09/13

import pandas as pd 
import numpy as np 
import quaternion
import pickle
import time
import os
import tempfile
import traceback
from pathlib import Path

# Updated imports for the new structure
from constants import constant_common, constant_mt, constant_mocap
from utils import common, alignment
from utils.mt import preprocessing_mt, calibration_mt, ik_mt


def mt_ik_in_memory(selected_setup, f_type, dim, subject, task, remove_offset, calibration_data, main_task_data):
    """
    In-memory version of mt_ik for web application use.
    Uses provided data instead of reading from files.
    """
    try:
        print(f"Subject={subject}, Task={task}, Setup={selected_setup}, Filter={f_type}, Dim={dim}, remove_offset={remove_offset}")
        
        f_params = common.get_filter_params(f_type)
        
        # Map calibration tasks based on detected task names (flexible assignment)
        data_static = None
        data_walking = None  
        data_jumping = None
        
        for task_id, task_data in calibration_data.items():
            if not task_data:
                continue
            
            # Determine task type based on folder name from sensor keys
            task_name = ""
            if task_data:
                # Get task name from the first sensor's key (extract folder name)
                first_sensor_key = list(task_data.keys())[0]
                if '/' in first_sensor_key:
                    task_name = first_sensor_key.split('/')[0].lower()
            
            print(f"DEBUG: Processing calibration task {task_id} with detected name: '{task_name}'")
            
            # Map based on task name keywords
            if any(keyword in task_name for keyword in ['static', 'standing', 'pose']):
                data_static = task_data
                print(f"DEBUG: Using task {task_id} ('{task_name}') as static calibration")
            elif any(keyword in task_name for keyword in ['walking', 'treadmill', 'gait']):
                data_walking = task_data
                print(f"DEBUG: Using task {task_id} ('{task_name}') as walking calibration")
            elif any(keyword in task_name for keyword in ['jump', 'squat', 'cmj']):
                data_jumping = task_data
                print(f"DEBUG: Using task {task_id} ('{task_name}') as jumping/squat calibration")
            else:
                # Fallback: assign to the first available slot
                if data_static is None:
                    data_static = task_data
                    print(f"DEBUG: Using task {task_id} ('{task_name}') as static calibration (fallback)")
                elif data_walking is None:
                    data_walking = task_data
                    print(f"DEBUG: Using task {task_id} ('{task_name}') as walking calibration (fallback)")
        
        # Ensure we have at least static data
        if data_static is None:
            # Use any available task as static data
            for task_id, task_data in calibration_data.items():
                if task_data:
                    data_static = task_data
                    print(f"DEBUG: Using task {task_id} as static calibration (emergency fallback)")
                    break
        
        # Validate we have required calibration data
        if not data_static:
            raise ValueError("No static calibration data found. Please upload a calibration task with 'static', 'standing', or 'pose' in the name.")
        
        # Convert data to proper format (DataFrames)
        data_static = match_data_in_memory(data_static)
        data_walking = match_data_in_memory(data_walking) if data_walking else {}
        data_jumping = match_data_in_memory(data_jumping) if data_jumping else {}
        
        print(f"DEBUG: Calibration data prepared - Static: {bool(data_static)}, Walking: {bool(data_walking)}, Jumping: {bool(data_jumping)}")

        # Determine walking period for calibration
        walking_period = [0, 1000]  # fallback
        if data_walking and "shank_r" in data_walking:
            if selected_setup[0].upper() == 'F':
                gyr_key = "Gyr_Y"
            else:
                gyr_key = "Gyr_Z"
                
            if gyr_key in data_walking["shank_r"]:
                try:
                    gyr_data = np.array(data_walking["shank_r"][gyr_key])
                    walking_period = calibration_mt.get_walking_4_calib(gyr_data)
                    print(f"DEBUG: Walking period detected: {walking_period}")
                except Exception as e:
                    print(f"DEBUG: Could not detect walking period, using fallback: {e}")
                    # Use a reasonable portion of the data
                    data_length = len(data_walking["shank_r"][gyr_key])
                    walking_period = [int(0.1 * data_length), int(0.9 * data_length)]
                    print(f"DEBUG: Walking period fallback: {walking_period}")
        else:
            print("DEBUG: No walking data or shank_r sensor, using static data for walking calibration")

        # Set jumping period (use static data if no jumping data available)
        if data_jumping and "pelvis" in data_jumping and "Gyr_Y" in data_jumping["pelvis"]:
            jumping_period = [0, len(data_jumping["pelvis"]["Gyr_Y"])]
        else:
            # Use static data as fallback for jumping period
            if data_static and "pelvis" in data_static and "Gyr_Y" in data_static["pelvis"]:
                jumping_period = [0, len(data_static["pelvis"]["Gyr_Y"])]
            else:
                jumping_period = [0, 100]  # minimal fallback
        
        print(f"DEBUG: Periods - Walking: {walking_period}, Jumping: {jumping_period}")

        # Perform sensor-to-segment calibration
        seg2sens = calibration_mt.sensor_to_segment_mt(
            data_static, 
            data_walking if data_walking else data_static,  # Use static as fallback for walking
            walking_period,
            data_jumping if data_jumping else data_static,  # Use static as fallback for jumping
            jumping_period, 
            selected_setup
        )
        
        print(f"DEBUG: seg2sens computed with keys: {list(seg2sens.keys())}")
        print("DEBUG: Sensor-to-segment transformation computed")

        # Handle 6D case
        if dim.upper() == '6D':
            print('(Perfect standing assumption for 6D filters)')
            initial_orientation = {}
            for sensor_name in seg2sens.keys():
                initial_orientation[sensor_name] = quaternion.from_rotation_matrix(np.identity(3))*quaternion.from_rotation_matrix(seg2sens[sensor_name])

        # Find static offsets if requested
        static_offset_mt = None
        if remove_offset:
            print('- Find static offsets')
            static_orientation_mt = ik_mt.get_imu_orientation_mt(
                data_static, f_type=f_type, fs=constant_mt.MT_SAMPLING_RATE, 
                dim=dim.upper(), params=f_params
            )
            
            if dim.upper() == '6D':
                static_orientation_mt = calibration_mt.correct_random_6D_orientation(initial_orientation, static_orientation_mt)
                
            static_ja_mt = ik_mt.get_all_ja_mt(seg2sens, static_orientation_mt)
            static_offset_mt = ik_mt.get_static_offset_mt(static_ja_mt)

        # Process main task data
        data_main = match_data_in_memory(main_task_data)
        print('- Estimate joint angles')
        
        orientation_mt, time_mt = ik_mt.get_imu_orientation_mt(
            data_main, f_type=f_type, fs=constant_mt.MT_SAMPLING_RATE, 
            dim=dim.upper(), params=f_params, get_time=True
        )
        
        if dim.upper() == '6D':
            orientation_mt = calibration_mt.correct_random_6D_orientation(initial_orientation, orientation_mt)
            
        ja_mt = ik_mt.get_all_ja_mt(seg2sens, orientation_mt)

        # Apply static offset removal if requested
        if remove_offset and static_offset_mt is not None:
            print('- Remove offsets')
            for joint in ja_mt.keys():
                ja_mt[joint] = ja_mt[joint] - static_offset_mt.get(joint, 0)

        # Apply alignment to convert from Earth frame to OpenSim coordinate system
        print('- Apply alignment for OpenSim coordinate system')
        # Use the static period for alignment (first 10% of data, minimum 10 samples)
        data_length = len(ja_mt['pelvis_tilt'])
        alignment_end = max(10, int(0.1 * data_length))
        alignment_period = [0, min(alignment_end, data_length - 1)]
        aligned_ja_mt = alignment.get_ja_alignment(ja_mt, alignment_period)
        
        # Return aligned results
        results = {"joint_angles": aligned_ja_mt, "time": time_mt}
        print("*** mt_ik_in_memory complete ***")
        return results

    except Exception as e:
        print(f"Error in mt_ik_in_memory: {e}")
        traceback.print_exc()
        return {"error": str(e)}


def match_data_in_memory(data_dict):
    """
    Format data for in-memory processing.
    Converts sensor data to DataFrames for IK processing.
    """
    if not data_dict:
        return {}
        
    formatted_data = {}
    for sensor_name, sensor_data in data_dict.items():
        # Convert to DataFrame if it's a dictionary
        if isinstance(sensor_data, dict):
            formatted_data[sensor_name] = pd.DataFrame(sensor_data)
        elif isinstance(sensor_data, pd.DataFrame):
            formatted_data[sensor_name] = sensor_data
        else:
            # Try to convert to DataFrame
            formatted_data[sensor_name] = pd.DataFrame(sensor_data)
    return formatted_data


def mt_ik(selected_setup, f_type, dim, subject, task, remove_offset, source='mt'):
    ''' Get joint angles from MTw data 
    
    Args:
       + selected_setup (str): sensor placement, i.e., 'mm' (for main analysis), 'hh', 'll', or 'ff'
       + f_type (str): filter type, i.e., 'Xsens', 'MAH', 'VQF', 'MAD', or 'EKF'
       + dim (str): dimension of the data, i.e., '9D' or '6D'
       + subject (int): subject number
       + task (str): task being performed
       + remove_offset (bool): remove offset from the data

    Returns:
       + NA
    '''
    
    if source == 'mt':
        subject_list = common.get_subject_list(subject)
        task_list    = common.get_task_list(task)
        filter_list  = common.get_filter_list(f_type, dim.upper())
    elif source == 'mt_long':
        subject_list = common.get_subject_list_long(subject)
        task_list    = common.get_task_list_long(task)
        filter_list  = common.get_filter_list(f_type, dim.upper())

    for f_type in filter_list:
        print('*** Filter ' + f_type)

        for subject in subject_list:
            print('*** Subject ' + str(subject))
            print('*** Sensor axes ' + dim.upper())

            try:
                f_params = common.get_filter_params(f_type)

                sensor_config  = {'pelvis': 'PELVIS', 
                                'foot_r': 'FOOT_R', 'shank_r': 'SHANK_R_' + selected_setup[0].upper(), 'thigh_r': 'THIGH_R_' + selected_setup[1].upper(),
                                'foot_l': 'FOOT_L', 'shank_l': 'SHANK_L_' + selected_setup[0].upper(), 'thigh_l': 'THIGH_L_' + selected_setup[1].upper()}

                print('- Find sensor-to-segment calibration')
                task_static     = 'static'
                data_static_mt  = preprocessing_mt.get_all_data_mt(subject, task_static, sensor_config)
                data_static_mt  = preprocessing_mt.match_data_mt(data_static_mt) 
                task_walking    = 'treadmill_walking' 
                data_walking_mt = preprocessing_mt.get_all_data_mt(subject, task_walking, sensor_config)
                task_jumping    = 'cmj' 
                data_jumping_mt = preprocessing_mt.get_all_data_mt(subject, task_jumping, sensor_config)

                if selected_setup[0].upper() == 'F':
                    walking_period = calibration_mt.get_walking_4_calib(data_walking_mt['shank_r']['Gyr_Y'].to_numpy())
                else:
                    walking_period = calibration_mt.get_walking_4_calib(data_walking_mt['shank_r']['Gyr_Z'].to_numpy())
                
                jumping_period = [0, data_jumping_mt['pelvis']['Gyr_Y'].shape[0]]

                seg2sens = calibration_mt.sensor_to_segment_mt(data_static_mt, data_walking_mt, walking_period, data_jumping_mt, jumping_period, selected_setup)

                if dim.upper() == '6D':
                    print('(Perfect standing assumption for 6D filters)')
                    initial_orientation = {}
                    for sensor_name in seg2sens.keys():
                        initial_orientation[sensor_name] = quaternion.from_rotation_matrix(np.identity(3))*quaternion.from_rotation_matrix(seg2sens[sensor_name])

                if remove_offset:
                    print('- Find static offsets')
                    if source == 'mt':
                        static_orientation_mt = ik_mt.get_imu_orientation_mt(data_static_mt, f_type = f_type, fs = constant_mt.MT_SAMPLING_RATE, dim = dim.upper(), params = f_params)
                    elif source == 'mt_long':
                        static_orientation_mt = ik_mt.get_imu_orientation_mt(data_static_mt, f_type = f_type, fs = constant_mocap.MOCAP_SAMPLING_RATE, dim = dim.upper(), params = f_params)

                    if dim.upper() == '6D':
                        if source == 'mt':
                            static_orientation_mt = calibration_mt.correct_random_6D_orientation(initial_orientation, static_orientation_mt)
                        elif source == 'mt_long':
                            static_orientation_mt = calibration_mt.correct_random_6D_orientation(initial_orientation, static_orientation_mt, fs = constant_mocap.MOCAP_SAMPLING_RATE)
                    static_ja_mt          = ik_mt.get_all_ja_mt(seg2sens, static_orientation_mt)
                    static_offset_mt      = ik_mt.get_static_offset_mt(static_ja_mt) 

                for selected_task in [task]:  # Process only the requested task
                    print('*** TASK: ' + selected_task)
                    
                    try:
                        # Use provided main task data instead of loading from files
                        data_main_mt = match_data_in_memory(main_task_data)

                        print('- Estimate joint angles')
                        if source == 'mt':
                            orientation_mt, time_mt = ik_mt.get_imu_orientation_mt(data_main_mt, f_type = f_type, fs = constant_mt.MT_SAMPLING_RATE, dim = dim.upper(), params = f_params, get_time = True)
                        elif source == 'mt_long':
                            orientation_mt, time_mt = ik_mt.get_imu_orientation_mt(data_main_mt, f_type = f_type, fs = constant_mocap.MOCAP_SAMPLING_RATE, dim = dim.upper(), params = f_params, get_time = True)

                        if dim.upper() == '6D':
                            if source == 'mt':
                                orientation_mt = calibration_mt.correct_random_6D_orientation(initial_orientation, orientation_mt)
                            elif source == 'mt_long':
                                orientation_mt = calibration_mt.correct_random_6D_orientation(initial_orientation, orientation_mt, fs = constant_mocap.MOCAP_SAMPLING_RATE)
                        ja_mt = ik_mt.get_all_ja_mt(seg2sens, orientation_mt)

                        if remove_offset:
                            print('- Remove offsets') 
                            for joint in ja_mt.keys():
                                ja_mt[joint] = ja_mt[joint] - static_offset_mt[joint]

                        # Apply alignment to convert from Earth frame to OpenSim coordinate system
                        print('- Apply alignment for OpenSim coordinate system')
                        # Use the static period for alignment (first 10% of data, minimum 10 samples)
                        data_length = len(ja_mt['pelvis_tilt'])
                        alignment_end = max(10, int(0.1 * data_length))
                        alignment_period = [0, min(alignment_end, data_length - 1)]
                        aligned_ja_mt = alignment.get_ja_alignment(ja_mt, alignment_period)
                        
                        # Return aligned results
                        results = {"joint_angles": aligned_ja_mt, "time": time_mt}
                        print("*** mt_ik_in_memory complete ***")
                        return results

                    except Exception as e:
                        print(f'*** Error in processing {selected_task}: {e}')
                        traceback.print_exc()
                        return {"error": str(e)}

            except Exception as e:
                print(f"Error in mt_ik_in_memory: {e}")
                traceback.print_exc()
                return {"error": str(e)}


def match_data_in_memory(data_dict):
    """
    Format data for in-memory processing.
    Converts sensor data to DataFrames for IK processing.
    """
    if not data_dict:
        return {}
        
    formatted_data = {}
    for sensor_name, sensor_data in data_dict.items():
        # Convert to DataFrame if it's a dictionary
        if isinstance(sensor_data, dict):
            formatted_data[sensor_name] = pd.DataFrame(sensor_data)
        elif isinstance(sensor_data, pd.DataFrame):
            formatted_data[sensor_name] = sensor_data
        else:
            # Try to convert to DataFrame
            formatted_data[sensor_name] = pd.DataFrame(sensor_data)
    return formatted_data






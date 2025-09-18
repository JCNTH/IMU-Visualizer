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
import sys
sys.path.append(str(Path(__file__).parent.parent))

from constants import constant_common, constant_mt, constant_mocap
from utils import common
from utils.mt import preprocessing_mt, calibration_mt, ik_mt

def mt_ik_in_memory(selected_setup, f_type, dim, subject, task, remove_offset,
                    calibration_data: dict,
                    main_task_data: dict):
    """
    In-memory version of the MT IK processing for web application use.
    
    Args:
        selected_setup (str): sensor placement, i.e., 'mm', 'hh', 'll', or 'ff'
        f_type (str): filter type, i.e., 'Xsens', 'MAH', 'VQF', 'MAD', or 'EKF'
        dim (str): dimension of the data, i.e., '9D' or '6D'
        subject (int): subject number
        task (str): task being performed
        remove_offset (bool): remove offset from the data
        calibration_data (dict): calibration data by task name
        main_task_data (dict): main task sensor data
        
    Returns:
        dict: Results containing joint angles and timing data
    """
    try:
        print("*** Running mt_ik_in_memory ***")
        print(f"Subject={subject}, Task={task}, Setup={selected_setup}, Filter={f_type}, Dim={dim}, remove_offset={remove_offset}")

        # Get filter parameters
        f_params = common.get_filter_params(f_type)
        
        # Configure sensor setup
        sensor_config = {
            'pelvis': 'PELVIS', 
            'foot_r': 'FOOT_R', 'shank_r': 'SHANK_R_' + selected_setup[0].upper(), 'thigh_r': 'THIGH_R_' + selected_setup[1].upper(),
            'foot_l': 'FOOT_L', 'shank_l': 'SHANK_L_' + selected_setup[0].upper(), 'thigh_l': 'THIGH_L_' + selected_setup[1].upper()
        }

        # Extract calibration data for different tasks
        data_static = calibration_data.get("static", {})
        data_walking = calibration_data.get("treadmill_walking", {})
        data_jumping = calibration_data.get("cmj", {})

        # Convert data to proper format
        data_static = match_data_in_memory(data_static)
        data_walking = match_data_in_memory(data_walking)
        data_jumping = match_data_in_memory(data_jumping) if data_jumping else {}

        # Determine walking period for calibration
        walking_period = [0, 1000]  # fallback
        if data_walking and "shank_r" in data_walking:
            if selected_setup[0].upper() == 'F':
                gyr_key = "Gyr_Y"
            else:
                gyr_key = "Gyr_Z"
                
            if gyr_key in data_walking["shank_r"]:
                gyr_data = np.array(data_walking["shank_r"][gyr_key])
                walking_period = calibration_mt.get_walking_4_calib(gyr_data)
                print(f"DEBUG: Walking period set to: {walking_period}")

        # Set jumping period
        jumping_period = [0, len(data_jumping.get("pelvis", {}).get("Gyr_Y", [0]))] if data_jumping else [0, 0]

        # Perform sensor-to-segment calibration
        seg2sens = calibration_mt.sensor_to_segment_mt(
            data_static, data_walking, walking_period,
            data_jumping if data_jumping else data_static, jumping_period, selected_setup
        )
        
        print("DEBUG: Sensor-to-segment transformation computed")

        # Handle 6D case
        if dim.upper() == '6D':
            print('(Perfect standing assumption for 6D filters)')
            initial_orientation = {}
            for sensor_name in seg2sens.keys():
                initial_orientation[sensor_name] = quaternion.from_rotation_matrix(np.identity(3)) * quaternion.from_rotation_matrix(seg2sens[sensor_name])

        # Compute static offset if requested
        static_offset_mt = None
        if remove_offset and data_static:
            print('- Find static offsets')
            static_orientation_mt = ik_mt.get_imu_orientation_mt(
                data_static, f_type=f_type, fs=constant_mt.MT_SAMPLING_RATE, 
                dim=dim.upper(), params=f_params
            )
            
            if dim.upper() == '6D':
                static_orientation_mt = calibration_mt.correct_random_6D_orientation(initial_orientation, static_orientation_mt)
                
            static_ja_mt = ik_mt.get_all_ja_mt(seg2sens, static_orientation_mt)
            static_offset_mt = ik_mt.get_static_offset_mt(static_ja_mt)
            print("DEBUG: Static offset computed")

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

        # Return results
        results = {"joint_angles": ja_mt, "time": time_mt}
        print("*** mt_ik_in_memory complete ***")
        return results

    except Exception as e:
        print("Error in mt_ik_in_memory:", str(e))
        traceback.print_exc()
        return {"error": str(e)}


def match_data_in_memory(data_dict):
    """
    Format data for in-memory processing.
    Converts lists to numpy arrays and ensures proper data structure.
    """
    if not data_dict:
        return {}
        
    formatted_data = {}
    for sensor_name, sensor_data in data_dict.items():
        formatted_data[sensor_name] = {}
        for column, values in sensor_data.items():
            if isinstance(values, list):
                formatted_data[sensor_name][column] = np.array(values)
            elif hasattr(values, 'to_numpy'):
                formatted_data[sensor_name][column] = values.to_numpy()
            else:
                formatted_data[sensor_name][column] = values
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

            for selected_task in task_list:
                print('*** TASK: ' + selected_task)
                
                try:
                    data_main_mt = preprocessing_mt.get_all_data_mt(subject, selected_task, sensor_config)
                    data_main_mt = preprocessing_mt.match_data_mt(data_main_mt)

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
                    ja_mt          = ik_mt.get_all_ja_mt(seg2sens, orientation_mt)

                    if remove_offset:
                        title_offset = '_roffset'
                        print('- Remove offsets') 
                        for joint in ja_mt.keys():
                            ja_mt[joint] = ja_mt[joint] - static_offset_mt[joint]
                    else:
                        title_offset = ''

                    if source == 'mt_long':
                        pass 
                    else:
                        print('- Apply synchronization') 
                        sync_fn = constant_common.OUT_SYNC_INFO + 'sync_info_s' + str(subject) + '_' + selected_task + '.pkl'
                        with open(sync_fn, 'rb') as f:
                            sync_info = pickle.load(f)

                        if sync_info['first_start'] == 'imu':
                            for joint in ja_mt.keys():
                                ja_mt[joint] = ja_mt[joint][sync_info['shifting_id']:]

                    print('- Save results of ' + selected_task)
                    common.mkfolder(constant_common.OUT_MT_JA_PATH)
                    if selected_setup == 'mm':
                        filename = constant_common.OUT_MT_JA_PATH + 'ik_s' + str(subject) + '_' + f_type.lower() + '_' + dim.upper() + '_' + selected_task + title_offset + '.pkl'
                    else:
                        filename = constant_common.OUT_MT_JA_PATH + 'ik_s' + str(subject) + '_' + f_type.lower() + '_' + dim.upper() + '_' + selected_task + '_' + selected_setup + title_offset + '.pkl'
                    with open(filename, 'wb') as f:
                        pickle.dump(ja_mt, f)
                    
                    if selected_setup == 'mm':
                        common.mkfolder(constant_common.OUT_MT_RUN_TIME_PATH)
                        if selected_setup == 'mm':
                            filename = constant_common.OUT_MT_RUN_TIME_PATH + 'ik_s' + str(subject) + '_' + f_type.lower() + '_' + dim.upper() + '_' + selected_task + title_offset + '.pkl'
                        else:
                            filename = constant_common.OUT_MT_RUN_TIME_PATH + 'ik_s' + str(subject) + '_' + f_type.lower() + '_' + dim.upper() + '_' + selected_task + '_' + selected_setup + title_offset + '.pkl'
                        with open(filename, 'wb') as f:
                            pickle.dump(time_mt, f)

                    print('\n\n\n\n\n')

                except:
                    print('*** Error in processing ' + selected_task)






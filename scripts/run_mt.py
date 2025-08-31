# run_mt.py
import pandas as pd 
import numpy as np 
import quaternion
import pickle
import time
import os
import tempfile
import traceback
from pathlib import Path

from utils.common import get_filter_params, get_subject_list, get_task_list, get_filter_list
from utils.mt.preprocessing_mt import get_all_data_mt, match_data_mt  # (not used in in‑memory version)
from utils.mt.calibration_mt import sensor_to_segment_mt, get_walking_4_calib, correct_random_6D_orientation
from utils.mt.ik_mt import get_imu_orientation_mt, get_all_ja_mt, get_static_offset_mt
from constants.constant_mt import MT_SAMPLING_RATE
from constants.constant_common import STATIC_STANDING_PERIOD

from constants import constant_common, constant_mt, constant_mocap
from utils import common
from utils.mt import preprocessing_mt, calibration_mt, ik_mt

global_calibration_data = None

def mt_ik_in_memory(selected_setup, f_type, dim, subject, task, remove_offset,
                    calibration_data: dict,
                    main_task_data: dict):
    try:
        print("*** Running mt_ik_in_memory ***")
        print(f"Subject={subject}, Task={task}, Setup={selected_setup}, Filter={f_type}, Dim={dim}, remove_offset={remove_offset}")

        # Extract calibration data for static and walking tasks.
        data_static = calibration_data.get("static", {})
        data_walking = calibration_data.get("treadmill_walking", {})
        data_jumping = calibration_data.get("cmj", {})  # may be empty if not used

        data_static = match_data_in_memory(data_static)
        data_walking = match_data_in_memory(data_walking)
        data_jumping = match_data_in_memory(data_jumping)

        # Determine the walking period (or use a fallback)
        walking_period = [0, 1000]  # fallback
        if "shank_r" in data_walking and "Gyr_Y" in data_walking["shank_r"]:
            gyr_data = np.array(data_walking["shank_r"]["Gyr_Y"])
            walking_period = calibration_mt.get_walking_4_calib(gyr_data)
            print(f"DEBUG: Walking period set to: {walking_period}")
        else:
            print("DEBUG: No valid shank_r data in walking; using fallback walking period.")

        # Calibrate sensor-to-segment alignment.
        seg2sens = calibration_mt.sensor_to_segment_mt(
            data_static, data_walking, walking_period,
            data_jumping, [0, 0], selected_setup
        )
        print("DEBUG: Sensor-to-segment transformation (seg2sens):")
        for sensor, mat in seg2sens.items():
            print(f"   {sensor}: {mat}")

        # Compute static offset if requested.
        if remove_offset and data_static:
            # Get the static orientation.
            static_orientation_mt = ik_mt.get_imu_orientation_mt(
                data_static, f_type=f_type, fs=MT_SAMPLING_RATE, dim=dim.upper()
            )
            # print("DEBUG: static_orientation_mt computed:")
            # print(static_orientation_mt)

            # Compute joint angles from static orientation.
            static_ja_mt = ik_mt.get_all_ja_mt(seg2sens, static_orientation_mt)
            # print("DEBUG: static joint angles (static_ja_mt) computed:")
            # print(static_ja_mt)

            # Compute the static offset.
            static_offset_mt = ik_mt.get_static_offset_mt(static_ja_mt)
            # print("DEBUG: static_offset_mt computed:")
            # print(static_offset_mt)
        else:
            static_offset_mt = None
            print("DEBUG: No static calibration offset computed.")

        # Process main task data.
        data_main = match_data_in_memory(main_task_data)
        orientation_mt, time_mt = ik_mt.get_imu_orientation_mt(
            data_main, f_type=f_type, fs=MT_SAMPLING_RATE, dim=dim.upper(), get_time=True
        )
        # Compute joint angles for the main task.
        ja_mt = ik_mt.get_all_ja_mt(seg2sens, orientation_mt)
        print("DEBUG: Main task joint angles computed (before offset removal):")
        print({joint: angles[:5] for joint, angles in ja_mt.items()})  # show first 5 values

        # Remove static offset if requested.
        if remove_offset and static_offset_mt is not None:
            for joint in ja_mt:
                ja_mt[joint] = ja_mt[joint] - static_offset_mt.get(joint, 0)
            print("DEBUG: Main task joint angles computed (after offset removal):")
            print({joint: angles[:5] for joint, angles in ja_mt.items()})
        else:
            print("DEBUG: Offset removal not applied.")

        results = {"joint_angles": ja_mt, "time": time_mt}
        print("*** mt_ik_in_memory complete ***")
        return results

    except Exception as e:
        print("Error in mt_ik_in_memory:", str(e))
        import traceback
        traceback.print_exc()
        return {"error": str(e)}



def match_data_in_memory(data_dict):
    """
    For in-memory calibration or main task data, perform any
    necessary reformatting or interpolation.
    
    Here, we simply pass the data through.
    """
    return data_dict

def mt_ik(selected_setup, f_type, dim, subject, task, remove_offset, source = 'mt'):
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

            # TODO: extract the selected setup

            sensor_config  = {'pelvis': 'PELVIS', 
                            'foot_r': 'FOOT_R', 'shank_r': 'SHANK_R_' + selected_setup[0].upper(), 'thigh_r': 'THIGH_R_' + selected_setup[1].upper(),
                            'foot_l': 'FOOT_L', 'shank_l': 'SHANK_L_' + selected_setup[0].upper(), 'thigh_l': 'THIGH_L_' + selected_setup[1].upper()}

            # print(sensor_config)
            # breakpoint()

            print('- Find sensor-to-segment calibration')
            task_static = 'static'
            if global_calibration_data is not None and "0" in global_calibration_data:
                data_static_mt = global_calibration_data["0"]
            else:
                data_static_mt = preprocessing_mt.get_all_data_mt(subject, task_static, sensor_config)

            task_walking = 'treadmill_walking'
            if global_calibration_data is not None and "1" in global_calibration_data:
                data_walking_mt = global_calibration_data["1"]
            else:
                data_walking_mt = preprocessing_mt.get_all_data_mt(subject, task_walking, sensor_config)

            task_jumping = 'cmj'
            # MODIFIED: Added try-except block to handle missing jumping data
            try:
                data_jumping_mt = preprocessing_mt.get_all_data_mt(subject, task_jumping, sensor_config)
                
                # Check if we have data for pelvis and Gyr_Y column
                if 'pelvis' in data_jumping_mt and 'Gyr_Y' in data_jumping_mt['pelvis']:
                    # Get the length of the data, handling both numpy arrays and lists
                    if hasattr(data_jumping_mt['pelvis']['Gyr_Y'], 'shape'):
                        jumping_period = [0, data_jumping_mt['pelvis']['Gyr_Y'].shape[0]]
                    else:
                        jumping_period = [0, len(data_jumping_mt['pelvis']['Gyr_Y'])]
                else:
                    jumping_period = [0, 0]
                    
                has_jumping_data = True
            except FileNotFoundError:
                print(f"Warning: Jumping data files not found for task '{task_jumping}'. Using static calibration only.")
                # Create an empty dictionary with the same structure as data_static_mt
                data_jumping_mt = {}
                for sensor_name in data_static_mt.keys():
                    data_jumping_mt[sensor_name] = {}
                    for column in data_static_mt[sensor_name].keys():
                        # Create empty arrays with same shape as static data
                        if hasattr(data_static_mt[sensor_name][column], 'shape'):
                            data_jumping_mt[sensor_name][column] = np.zeros_like(data_static_mt[sensor_name][column])
                        else:
                            data_jumping_mt[sensor_name][column] = [0] * len(data_static_mt[sensor_name][column])
                jumping_period = [0, 0]  # Empty period
                has_jumping_data = False

            # Determine the walking period for calibration
            # MODIFIED: Handle both numpy arrays and lists
            if selected_setup[0].upper() == 'F':
                gyr_data = data_walking_mt['shank_r']['Gyr_Y']
                # Convert to numpy array if it's a list
                if not hasattr(gyr_data, 'to_numpy'):
                    if isinstance(gyr_data, list):
                        gyr_data = np.array(gyr_data)
                    elif hasattr(gyr_data, 'values'):
                        gyr_data = gyr_data.values
                walking_period = calibration_mt.get_walking_4_calib(gyr_data)
            else:
                gyr_data = data_walking_mt['shank_r']['Gyr_Z']
                # Convert to numpy array if it's a list
                if not hasattr(gyr_data, 'to_numpy'):
                    if isinstance(gyr_data, list):
                        gyr_data = np.array(gyr_data)
                    elif hasattr(gyr_data, 'values'):
                        gyr_data = gyr_data.values
                walking_period = calibration_mt.get_walking_4_calib(gyr_data)
            
            # Define a helper function to ensure data is in the correct format
            def ensure_numpy_array(data_dict):
                result_dict = {}
                for sensor_name, sensor_data in data_dict.items():
                    result_dict[sensor_name] = {}
                    for column, values in sensor_data.items():
                        if isinstance(values, list):
                            result_dict[sensor_name][column] = np.array(values)
                        elif hasattr(values, 'to_numpy'):
                            result_dict[sensor_name][column] = values.to_numpy()
                        else:
                            result_dict[sensor_name][column] = values
                return result_dict
            
            # Convert data to ensure they are numpy arrays
            data_static_mt = ensure_numpy_array(data_static_mt)
            data_walking_mt = ensure_numpy_array(data_walking_mt)
            data_jumping_mt = ensure_numpy_array(data_jumping_mt)

            # MODIFIED: Use static_to_segment_mt function instead if jumping data is not available
            if has_jumping_data:
                seg2sens = calibration_mt.sensor_to_segment_mt(data_static_mt, data_walking_mt, walking_period, 
                                                               data_jumping_mt, jumping_period, selected_setup)
            else:
                # Fall back to calibration without jumping data
                # Note: You may need to check if sensor_to_segment_mt has a version that doesn't require jumping data
                # If not, you might need to modify that function as well
                seg2sens = calibration_mt.sensor_to_segment_mt(data_static_mt, data_walking_mt, walking_period, 
                                                               data_static_mt, [0, 0], selected_setup)

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
                    
                    # Convert main task data to ensure they are numpy arrays
                    data_main_mt = ensure_numpy_array(data_main_mt)

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
                        title_offset = '_roffset'
                        print('- Remove offsets') 
                        for joint in ja_mt.keys():
                            ja_mt[joint] = ja_mt[joint] - static_offset_mt[joint]
                    else:
                        title_offset = ''

                    # MODIFIED: Only apply synchronization if sync file exists
                    if source == 'mt_long':
                        pass 
                    else:
                        sync_fn = constant_common.OUT_SYNC_INFO + 'sync_info_s' + str(subject) + '_' + selected_task + '.pkl'
                        if os.path.exists(sync_fn):
                            print('- Apply synchronization') 
                            with open(sync_fn, 'rb') as f:
                                sync_info = pickle.load(f)

                            if sync_info['first_start'] == 'imu':
                                for joint in ja_mt.keys():
                                    ja_mt[joint] = ja_mt[joint][sync_info['shifting_id']:]
                        else:
                            print(f"Warning: Sync file not found at {sync_fn}. Skipping synchronization.")

                    # import matplotlib.pyplot as plt
                    # breakpoint()

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

                except Exception as e:
                    print(f'*** Error in processing {selected_task}: {str(e)}')
                    import traceback
                    print(traceback.format_exc())
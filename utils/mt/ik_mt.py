# ik_mt.py
import numpy as np
import quaternion
import math
import time
from tqdm import tqdm
from scipy.spatial.transform import Rotation as R

# --- Define default constants in case you don't import them elsewhere --- #
# (Replace these with your own constants if they already exist)
MT_SAMPLING_RATE = 40.0
JA_SIGN = {
    'hip_adduction_l': 1,
    'hip_rotation_l': 1,
    'hip_flexion_l': 1,
    'knee_flexion_l': 1,
    'ankle_angle_l': 1,
    'hip_adduction_r': 1,
    'hip_rotation_r': 1,
    'hip_flexion_r': 1,
    'knee_flexion_r': 1,
    'ankle_angle_r': 1
}


# --- Orientation estimation function --- #
import numpy as np
import quaternion
import time
from tqdm import tqdm

def get_imu_orientation_mt(imu_data_mt, f_type='Xsens', fs=40, dim='9D', params=None, get_time=False):
    """
    Get orientation from IMU data given as a dictionary of DataFrames.
    This function assumes that each sensor’s DataFrame has either the columns:
      ["Quat_q0", "Quat_q1", "Quat_q2", "Quat_q3"]
    or the alternative:
      ["Quat_W", "Quat_X", "Quat_Y", "Quat_Z"].
    
    If neither set is found, it warns and uses identity quaternions.
    
    Args:
      imu_data_mt (dict): keys are sensor names and values are DataFrames.
      f_type (str): filter type, e.g. "Xsens".
      fs (float): sampling frequency.
      dim (str): dimension string, e.g. "9D".
      params (dict): additional parameters.
      get_time (bool): if True, return per-sensor timing as well.
      
    Returns:
      If get_time is False:
          orientation_mt (dict): { sensor_name: quaternion array }.
      Otherwise:
          (orientation_mt, time_mt) with time_mt per sample.
    """
    orientation_mt = {}
    time_mt = {}
    print(f"fs = {fs}")
    
    for sensor_name in tqdm(imu_data_mt.keys(), desc="Processing sensors"):
        start_time = time.time()
        sensor_data = imu_data_mt[sensor_name]
        try:
            # If sensor_data is a DataFrame, remove extra spaces in column names.
            if hasattr(sensor_data, 'columns'):
                sensor_data.columns = sensor_data.columns.str.strip()
            
            
            # Try the original quaternion columns:
            if all(col in sensor_data.columns for col in ['Quat_q0', 'Quat_q1', 'Quat_q2', 'Quat_q3']):
                q_array = quaternion.as_quat_array(
                    sensor_data[['Quat_q0', 'Quat_q1', 'Quat_q2', 'Quat_q3']].to_numpy()
                )
                orientation_mt[sensor_name] = q_array
                print(f"  Using 'Quat_q0' columns for {sensor_name} (shape: {q_array.shape})")
            # Try the alternative quaternion columns:
            elif all(col in sensor_data.columns for col in ['Quat_W', 'Quat_X', 'Quat_Y', 'Quat_Z']):
                q_array = quaternion.as_quat_array(
                    sensor_data[['Quat_W', 'Quat_X', 'Quat_Y', 'Quat_Z']].to_numpy()
                )
                orientation_mt[sensor_name] = q_array
                print(f"  Using 'Quat_W' columns for {sensor_name} (shape: {q_array.shape})")
            else:
                print(f"Warning: No quaternion columns found for {sensor_name}.")
                n_samples = sensor_data.shape[0] if hasattr(sensor_data, 'shape') else 100
                orientation_mt[sensor_name] = np.array([quaternion.quaternion(1, 0, 0, 0)] * n_samples)
            
            time_mt[sensor_name] = (time.time() - start_time) / orientation_mt[sensor_name].shape[0]
        except Exception as e:
            print(f"Error processing orientation for sensor {sensor_name}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            n_samples = sensor_data.shape[0] if hasattr(sensor_data, 'shape') else 100
            orientation_mt[sensor_name] = np.array([quaternion.quaternion(1, 0, 0, 0)] * n_samples)
            time_mt[sensor_name] = (time.time() - start_time) / orientation_mt[sensor_name].shape[0]
            
    if get_time:
        return orientation_mt, time_mt
    else:
        return orientation_mt


# --- Convert quaternion to Euler angles --- #
def quat_to_euler(quat, to_deg=True):
    """
    Convert a quaternion to Euler angles (using an Xsens-style convention).

    Args:
        quat (np.array or quaternion.quaternion): quaternion (w, x, y, z)
        to_deg (bool): whether to convert to degrees

    Returns:
        (x_angle, y_angle, z_angle): tuple of Euler angles
    """
    # The following formulas are taken from the MTw_Awinda_User_Manual.pdf (page 77)
    # and assume a particular order of rotation. Adjust these as needed for your conventions.
    x_angle = math.atan2(2*quat.y*quat.z + 2*quat.w*quat.x,
                         2*quat.w**2 + 2*quat.z**2 - 1)
    # Clip the sine value for numerical safety
    sin_y = 2*quat.x*quat.z - 2*quat.w*quat.y
    sin_y = max(-1.0, min(1.0, sin_y))
    y_angle = math.asin(sin_y)
    z_angle = math.atan2(2*quat.x*quat.y + 2*quat.w*quat.z,
                         2*quat.w**2 + 2*quat.x**2 - 1)
    if to_deg:
        x_angle = np.rad2deg(x_angle)
        y_angle = np.rad2deg(y_angle)
        z_angle = np.rad2deg(z_angle)
    return [x_angle, y_angle, z_angle]


# --- Compute joint angles between two adjacent segments --- #
def get_ja(sframe_1, sframe_2, s2s_1, s2s_2, c_flag=True):
    """
    Compute joint angles given the sensor (IMU) orientations for two adjacent segments.

    Args:
        sframe_1, sframe_2 (np.array of quaternions, shape=(N,)): sensor orientations.
        s2s_1, s2s_2 (np.array, shape=(3,3)): segment-to-sensor transformation matrices.
        c_flag (bool): if True, apply calibration: remove sensor-to-segment misalignment.

    Returns:
        imu_ja (np.array, shape=(N, 3)): Euler angles representing the joint angles.
    """
    N = sframe_1.shape[0]
    # Convert the segment-to-sensor matrices to quaternions.
    q_s2s_1 = quaternion.from_rotation_matrix(s2s_1)
    q_s2s_2 = quaternion.from_rotation_matrix(s2s_2)

    if c_flag:
        # Remove the sensor-to-segment misalignment (calibration)
        segment_1 = np.array([sframe_1[i] * q_s2s_1.conjugate() for i in range(N)])
        segment_2 = np.array([sframe_2[i] * q_s2s_2.conjugate() for i in range(N)])
    else:
        segment_1 = sframe_1.copy()
        segment_2 = sframe_2.copy()
    
    # Compute the relative rotation between the two segments:
    joint_rot = np.array([segment_1[i].conjugate() * segment_2[i] for i in range(N)])
    # Convert each relative quaternion to a 3-element Euler angle vector.
    imu_ja = np.array([quat_to_euler(q) for q in joint_rot])
    # Optionally: check the shape is (N, 3)
    assert imu_ja.shape == (N, 3), f"Expected joint angle shape (N,3), got {imu_ja.shape}"
    return imu_ja


# --- Compute all joint angles from sensor orientations --- #
def get_all_ja_mt(seg2sens, orientation_mt, c_flag=True):
    """
    Compute all joint angles (for both left and right legs) from IMU orientations.

    Args:
        seg2sens (dict): Dictionary of segment-to-sensor transformation matrices.
                         Expected keys: 'pelvis', 'thigh_l', 'thigh_r', 'shank_l', 'shank_r', 'foot_l', 'foot_r'
        orientation_mt (dict): Dictionary of sensor orientations (quaternion arrays).
        c_flag (bool): if True, apply sensor-to-segment calibration correction.

    Returns:
        mt_ja (dict): Dictionary containing joint angles for the lower limb.
                      Expected keys: 'hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l',
                                     'knee_flexion_l', 'ankle_angle_l',
                                     'hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r',
                                     'knee_flexion_r', 'ankle_angle_r'
    """
    mt_ja = {}

    # Process left side: pelvis -> thigh_l -> shank_l -> foot_l
    temp_hip_l   = get_ja(orientation_mt['pelvis'], orientation_mt['thigh_l'],
                           seg2sens['pelvis'], seg2sens['thigh_l'], c_flag=c_flag)
    temp_knee_l  = get_ja(orientation_mt['thigh_l'], orientation_mt['shank_l'],
                           seg2sens['thigh_l'], seg2sens['shank_l'], c_flag=c_flag)
    temp_ankle_l = get_ja(orientation_mt['shank_l'], orientation_mt['foot_l'],
                           seg2sens['shank_l'], seg2sens['foot_l'], c_flag=c_flag)

    # In this example we assume that:
    #   - The 3rd Euler angle (index 2) of the pelvis-thigh relative rotation is hip flexion.
    #   - The 1st Euler angle (index 0) is hip adduction.
    #   - The 2nd Euler angle (index 1) is hip rotation (with a sign flip).
    mt_ja['hip_adduction_l'] = JA_SIGN['hip_adduction_l'] * temp_hip_l[:, 0]
    mt_ja['hip_rotation_l']  = - JA_SIGN['hip_rotation_l'] * temp_hip_l[:, 1]
    mt_ja['hip_flexion_l']   = JA_SIGN['hip_flexion_l'] * temp_hip_l[:, 2]
    mt_ja['knee_flexion_l']  = JA_SIGN['knee_flexion_l'] * temp_knee_l[:, 2]
    mt_ja['ankle_angle_l']   = JA_SIGN['ankle_angle_l']  * temp_ankle_l[:, 2]

    # Process right side: pelvis -> thigh_r -> shank_r -> foot_r
    temp_hip_r   = get_ja(orientation_mt['pelvis'], orientation_mt['thigh_r'],
                           seg2sens['pelvis'], seg2sens['thigh_r'], c_flag=c_flag)
    temp_knee_r  = get_ja(orientation_mt['thigh_r'], orientation_mt['shank_r'],
                           seg2sens['thigh_r'], seg2sens['shank_r'], c_flag=c_flag)
    temp_ankle_r = get_ja(orientation_mt['shank_r'], orientation_mt['foot_r'],
                           seg2sens['shank_r'], seg2sens['foot_r'], c_flag=c_flag)

    mt_ja['hip_adduction_r'] = JA_SIGN['hip_adduction_r'] * temp_hip_r[:, 0]
    mt_ja['hip_rotation_r']  = - JA_SIGN['hip_rotation_r'] * temp_hip_r[:, 1]
    mt_ja['hip_flexion_r']   = JA_SIGN['hip_flexion_r'] * temp_hip_r[:, 2]
    mt_ja['knee_flexion_r']  = JA_SIGN['knee_flexion_r'] * temp_knee_r[:, 2]
    mt_ja['ankle_angle_r']   = JA_SIGN['ankle_angle_r']  * temp_ankle_r[:, 2]

    return mt_ja


# --- Compute static offset from static joint angles --- #
def get_static_offset_mt(static_ja_mt):
    """
    Compute the static offset from the static joint angles

    Args:
        static_ja_mt (dict): Dictionary with static joint angles arrays.

    Returns:
        static_offset_mt (dict): Dictionary with the mean (offset) for each joint.
    """
    static_offset_mt = {}
    for joint, angles in static_ja_mt.items():
        static_offset_mt[joint] = np.mean(angles)
    return static_offset_mt


import pandas as pd



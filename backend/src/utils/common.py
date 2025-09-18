# name: common.py
# description: Contain common functions for use
# author: Vu Phan
# date: 2023/06/05


import os
import math
import numpy as np 
from scipy.spatial.transform import Rotation as R

from imu_benchmark.constants import constant_common, constant_mt


# --- Make folder if not existing --- #
def mkfolder(path):
	''' Create a folder in the given path if not exist '''
	
	if not os.path.exists(path):
		os.makedirs(path)


# --- Configurate data processing --- #
def check_filter_config(f_type, dim):
    ''' Check the filter configuration '''

    if f_type in constant_mt.MT_FILTER_LIST[dim.upper()]:
        filter_config_check = True
        error_msg = None
    else:
        filter_config_check = False 
        error_msg = f_type + ' filter does not have ' + dim.upper() + ' option'

    return filter_config_check, error_msg


def get_subject_list(subject):
    ''' Get the list of subjects for processing data '''

    if subject == None:
        subject_list = constant_common.SUBJECT_LIST 
    else:
        subject_list = [subject]

    return subject_list


def get_subject_list_long(subject):
    ''' Get the list of subjects for processing data (long trials) '''

    if subject == None:
        subject_list = ['4l', '5l', '6l', '13l', '23l'] # HARDCODED: only for 5 subjects
    else:
        subject_list = [subject]

    return subject_list


def get_task_list(task):
	''' Get the list of tasks for processing data '''

	if task == None:
		task_list = list(constant_common.MAPPING_TASK_TO_ID.keys())[1::]
	else:
		task_list = [task]

	return task_list


def get_task_list_mvn(task):
    ''' Get the list of tasks for processing data (MVN) '''

    if task == None:
        task_list = ['sts_x', 'walking_x', 'running_x'] # HARDCODED: only for 3 tasks
    else:
        task_list = [task]

    return task_list


def get_task_list_long(task):
    ''' Get the list of tasks for processing data (long trials) '''

    if task == None:
        task_list = ['long_walk1', 'long_walk2', 'long_walk3'] # HARDCODED: only for 3 trials
    else:
        task_list = [task]

    return task_list


def get_filter_list(f_type, dim):
    ''' Get the list of filters for processing data '''

    if f_type == None:
        filter_list = constant_mt.MT_FILTER_LIST[dim.upper()]
    else:
        filter_list = [f_type]

    return filter_list


def get_filter_params(f_type):
    ''' Get the tuned parameters of the filter '''

    if f_type.upper() in constant_mt.MT_TUNED_PARAMS.keys():
        f_params = constant_mt.MT_TUNED_PARAMS[f_type.upper()]
    else:
        f_params = None

    return f_params


def get_sync_id(subject):
    ''' Get the synchronization ID for the subject (run synchronizer.py to obtain this) '''
    pass # tbd


# --- IMU configurations --- #
def config_imu_placement(subject):
	''' Get IMU ID '''

	imu_placement_id = {'torso_imu': constant_mt.LAB_IMU_NAME_MAP['CHEST'], 'pelvis_imu': constant_mt.LAB_IMU_NAME_MAP['PELVIS'], 
						'calcn_r_imu': constant_mt.LAB_IMU_NAME_MAP['FOOT_R'], 'tibia_r_imu': constant_mt.LAB_IMU_NAME_MAP['SHANK_R_MID'], 'femur_r_imu': constant_mt.LAB_IMU_NAME_MAP['THIGH_R_MID'],
						'calcn_l_imu': constant_mt.LAB_IMU_NAME_MAP['FOOT_L'], 'tibia_l_imu': constant_mt.LAB_IMU_NAME_MAP['SHANK_L_MID'], 'femur_l_imu': constant_mt.LAB_IMU_NAME_MAP['THIGH_L_MID']} 
	
	return imu_placement_id


# --- Conversion to Euler angles --- #
# From quaternions of Xsens sensors
# Source: MTw_Awinda_User_Manual.pdf (page 77)
def quat_to_euler(quat):
    ''' Convert a quaternion to Euler angles (Xsens sensor) '''

    angle_x = np.rad2deg(math.atan2(2*quat[2]*quat[3] + 2*quat[0]*quat[1], 2*quat[0]**2 + 2*quat[3]**2 - 1))
    angle_y = np.rad2deg(math.asin(2*quat[1]*quat[3] - 2*quat[0]*quat[2]))
    angle_z = np.rad2deg(math.atan2(2*quat[1]*quat[2] + 2*quat[0]*quat[3], 2*quat[0]**2 + 2*quat[1]**2 - 1))

    angle = np.array([angle_x, angle_y, angle_z])

    return angle


# From rotation matrices
def rotmat_to_angle(rotmat):
	''' Convert a rotation matrix to Euler angles '''
	
	r     = R.from_matrix(rotmat)
	angle = r.as_euler('xyz', degrees = True)

	return angle





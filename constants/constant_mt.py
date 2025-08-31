# name: constant_mt.py
# description: constants for Xsens IMUs
# author: Vu Phan
# date: 2024/01/24


# --- Physical constants --- #
EARTH_G_ACC = 9.81 # m/s^2


# --- Experimental setup --- #
# Main experiment
MT_SAMPLING_RATE = 40 # Hz


# --- MTw processing --- #
# Tuned parameters
MT_TUNED_PARAMS = {'MAD': [0.1], 'MAH': [0.4, 0.3], 'EKF': [0.9, 0.9, 0.9], 'VQF': [2, 10]}

# Filter list
MT_FILTER_LIST = {'9D': ['Xsens', 'VQF', 'MAD', 'MAH', 'EKF'], 
                  '6D': ['VQF', 'MAD', 'MAH', 'EKF', 'RIANN']}

# Calibration tasks
MT_CALIBRATION_TASKS = ['static', 'treadmill_walking', 'cmj']


# Sensor id
LAB_IMU_NAME_MAP = {'CHEST':     '00B4D7D4',
                    'PELVIS':    '00B4D7D3', 
                    'THIGH_L_M': '00B4D7FD', 
                    'SHANK_L_M': '00B4D7CE', 
                    'FOOT_L':    '00B4D7FF', 
                    'THIGH_R_M': '00B4D6D1', 
                    'SHANK_R_M': '00B4D7FB', 
                    'FOOT_R':    '00B4D7FE',
                    'THIGH_R_H': '00B4D7D0', 
                    'THIGH_R_L': '00B4D7D8', 
                    'THIGH_R_F': '00B4D7D1', 
                    'SHANK_R_H': '00B4D7BA', 
                    'SHANK_R_L': '00B4D7D5', 
                    'SHANK_R_F': '00B42961', 
                    'THIGH_L_H': '00B4D7D2', 
                    'THIGH_L_L': '00B4D7CD', 
                    'THIGH_L_F': '00B4D7D6',
                    'SHANK_L_H': '00B4D7CF', 
                    'SHANK_L_L': '00B4D7FA', 
                    'SHANK_L_F': '00B42991'}


# For OpenSense
MT_TO_OPENSENSE_MAP = {'pelvis': 'pelvis_imu',
                       'foot_r': 'calcn_r_imu', 'shank_r': 'tibia_r_imu', 'thigh_r': 'femur_r_imu',
                       'foot_l': 'calcn_l_imu', 'shank_l': 'tibia_l_imu', 'thigh_l': 'femur_l_imu'}


# --- Long trial period --- #
# Trial indices
LONG_TRIAL_ID = {'4l': {'t1': {'trial_start': 0, 'trial_end':  95200, 'sitting_start': 63000, 'sitting_end': 94300},
                        't2': {'trial_start': 183000, 'trial_end':  279400, 'sitting_start': 247800, 'sitting_end': 278200},
                        't3': {'trial_start': 369000, 'trial_end':  462200, 'sitting_start': 431400, 'sitting_end': 460800}},
                 '5l': {'t1': {'trial_start': 0, 'trial_end':  95000, 'sitting_start': 64300, 'sitting_end': 93000},
                        't2': {'trial_start': 181000, 'trial_end':  273200, 'sitting_start': 248500, 'sitting_end': 271500},
                        't3': {'trial_start': 357000, 'trial_end':  452500, 'sitting_start': 423000, 'sitting_end': 451000}},
                 '6l': {'t1': {'trial_start': 0, 'trial_end':  100000, 'sitting_start': 62500, 'sitting_end': 97800},
                        't2': {'trial_start': 197000, 'trial_end':  295000, 'sitting_start': 260000, 'sitting_end': 291600},
                        't3': {'trial_start': 386000, 'trial_end':  -1, 'sitting_start': 449250, 'sitting_end': 478000}},
                 '13l': {'t1': {'trial_start': 0, 'trial_end':  93500, 'sitting_start': 62400, 'sitting_end': 91750},
                         't2': {'trial_start': 174000, 'trial_end':  269300, 'sitting_start': 242000, 'sitting_end': 267500},
                         't3': {'trial_start': 355500, 'trial_end':  -1, 'sitting_start': 419000, 'sitting_end': 452000}},
                 '23l': {'t1': {'trial_start': 0, 'trial_end':  98000, 'sitting_start': 64000, 'sitting_end': 94200},
                         't2': {'trial_start': 187400, 'trial_end':  279500, 'sitting_start': 251800, 'sitting_end': 278600},
                         't3': {'trial_start': 371600, 'trial_end':  -1, 'sitting_start': 435400, 'sitting_end': -1}}}









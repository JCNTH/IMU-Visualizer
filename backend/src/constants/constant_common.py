# name: constant_common.py
# description: common constants used in processing
# author: Vu Phan
# date: 2024/01/27


# --- Directory --- #
IN_LAB_PATH = 'imu_benchmark/data/'
MT_PATH     = 'imu_data/'
MOCAP_PATH  = 'mocap_data/'
MOCAP_OPENSIM_PATH = 'mocap_ik/'

OPENSENSE_ASSET_PATH = 'imu_benchmark/opensense_assets/'


# --- Output --- #
OUT_MT_JA_PATH        = 'imu_benchmark/outputs/joint_angles/mt/'
OUT_MT_RUN_TIME_PATH  = 'imu_benchmark/outputs/run_time/mt/'
OUT_MOCAP_JA_PATH     = 'imu_benchmark/outputs/joint_angles/mocap/'
OUT_OPENSENSE_JA_PATH = 'imu_benchmark/outputs/joint_angles/opensense/'
OUT_MVN_JA_PATH        = 'imu_benchmark/outputs/joint_angles/mvn/'

OUT_OPENSENSE_PATH = 'imu_benchmark/outputs/os_ik/'

OUT_SYNC_INFO = 'imu_benchmark/outputs/sync_info/'

OUT_RMSE_PATH = 'imu_benchmark/outputs/rmse/'

OUT_EXERCISE_INDEX_PATH = 'imu_benchmark/outputs/exercise_index/'


# --- File format --- #
MT_EXTENSION    = '.txt'
MVN_EXTENSION   = '.xlsx'
MOCAP_EXTENSION = '.csv'


# --- Experiment parameters --- #
STATIC_STANDING_PERIOD = 3 # s

NUM_EXERCISE_REPS = 3 # number of repetitions for each (non-locomotion) exercise


# -- Data processing --- #
# Subject list
# SUBJECT_LIST = [4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
SUBJECT_LIST = [4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25]


# --- Name mapping --- #
# Task
LAB_TASK_NAME_MAP = {'static':            't0_static_pose_001',
                     'walking':           't1_walking_001',
                     'treadmill_walking': 't2_treadmill_walking_001',
                     'treadmill_running': 't3_treadmill_running_001',
                     'lat_step':          't4_lat_step_001',
                     'step_up_down':      't5_step_up_down_001',
                     'drop_jump':         't6_drop_jump_001',
                     'cmj':               't7_cmjdl_001',
                     'squat':             't8_squat_001',
                     'step_n_hold':       't9_step_n_hold_001',
                     'sls':               't10_sls_001',
                     'sts':               't11_sts_001', 
                     'long_walk1':        't12_longwalk_001',
                     'long_walk2':        't12_longwalk_002',
                     'long_walk3':        't12_longwalk_003',
                     'sts_x':             't13_xsens_sts_001',
                     'walking_x':         't13_xsens_treadmill_walking_001',
                     'running_x':         't13_xsens_treadmill_running_001'}

MAPPING_TASK_TO_ID = {'static':            0,
                     'walking':           1,
                     'treadmill_walking': 2,
                     'treadmill_running': 3,
                     'lat_step':          4,
                     'step_up_down':      5,
                     'drop_jump':         6,
                     'cmj':               7,
                     'squat':             8,
                     'step_n_hold':       9,
                     'sls':               10,
                     'sts':               11}

MAPPING_TASK_TO_ID_3 = {'static':            0,
                     'treadmill_walking': 2,
                     'treadmill_running': 3,
                     'sts':               11}

LIST_LOCOMOTION_TASK = ['walking', 'treadmill_walking', 'treadmill_running', 'long_walk1', 'long_walk2', 'long_walk3', 'running_x', 'walking_x']

# --- Kinematics signs --- #
# JA_SIGN = {'hip_adduction_l': -1, 'hip_rotation_l': -1, 'hip_flexion_l': 1,
#            'knee_adduction_l': -1, 'knee_rotation_l': -1, 'knee_flexion_l': -1, 
#            'ankle_angle_l': 1, 
#            'hip_adduction_r': 1, 'hip_rotation_r': 1, 'hip_flexion_r': 1,
#            'knee_adduction_r': 1, 'knee_rotation_r': 1, 'knee_flexion_r': -1,
#            'ankle_angle_r': 1}
JA_SIGN = {'pelvis_tilt': 1,        'pelvis_list': 1,       'pelvis_rot': 1,
           'hip_adduction_l': -1,   'hip_rotation_l': -1,   'hip_flexion_l': 1,
           'knee_adduction_l': -1,  'knee_rotation_l': -1,  'knee_flexion_l': -1, 
           'ankle_adduction_l': -1, 'ankle_rotation_l': -1, 'ankle_flexion_l': 1, 
           'hip_adduction_r': 1,    'hip_rotation_r': 1,    'hip_flexion_r': 1,
           'knee_adduction_r': 1,   'knee_rotation_r': 1,   'knee_flexion_r': -1,
           'ankle_adduction_r': 1,  'ankle_rotation_r': 1,  'ankle_flexion_r': 1}

# --- Tuning --- #
TUNING_SUBJECT_LIST = [2, 3]


# --- Data processing --- #
VERY_HIGH_NUMBER = 999 # to highlight the marker gaps in the processing






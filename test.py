# full_sample_data.py
import pandas as pd
from ik_solver import run_ik

def create_dummy_sensor_data(base_acc, base_gyro, base_mag, base_quat, rows=5):
    """
    Create a dummy DataFrame mimicking sensor output.
    
    Parameters:
      base_acc: baseline accelerometer value for Acc_X (other Acc_Y, Acc_Z will be offset).
      base_gyro: baseline gyroscope value for Gyr_X (others are derived similarly).
      base_mag: baseline magnetometer value for Mag_X.
      base_quat: baseline quaternion scalar for Quat_q0 (others are derived similarly).
      rows: number of time samples.
    
    Returns:
      A pandas DataFrame with columns for accelerometer, gyroscope, magnetometer, and quaternion values.
    """
    return pd.DataFrame({
        "Acc_X": [base_acc + i * 0.01 for i in range(rows)],
        "Acc_Y": [base_acc + 0.1 + i * 0.01 for i in range(rows)],
        "Acc_Z": [7.93 + i * 0.02 for i in range(rows)],
        "Gyr_X": [base_gyro + i * 0.001 for i in range(rows)],
        "Gyr_Y": [-(base_gyro) - i * 0.001 for i in range(rows)],
        "Gyr_Z": [0.001 + i * 0.001 for i in range(rows)],
        "Mag_X": [base_mag - i * 0.01 for i in range(rows)],
        "Mag_Y": [0.53 + i * 0.01 for i in range(rows)],
        "Mag_Z": [-0.41 - i * 0.01 for i in range(rows)],
        "Quat_q0": [base_quat + i * 0.01 for i in range(rows)],
        "Quat_q1": [-(base_quat) - i * 0.01 for i in range(rows)],
        "Quat_q2": [-(2 * base_quat) - i * 0.01 for i in range(rows)],
        "Quat_q3": [0.3 + i * 0.01 for i in range(rows)],
    })

# Create sample main task data for all sensors.
main_task_data = {
    "foot_r": create_dummy_sensor_data(5.5, 0.003, -0.57, 0.5),
    "foot_l": create_dummy_sensor_data(5.4, 0.003, -0.56, 0.5),
    "shank_r": create_dummy_sensor_data(9.7, 0.004, -0.70, 0.51),
    "shank_l": create_dummy_sensor_data(9.68, 0.004, -0.69, 0.51),
    "thigh_r": create_dummy_sensor_data(9.69, 0.004, -0.71, 0.51),
    "thigh_l": create_dummy_sensor_data(9.75, 0.004, -0.72, 0.51),
    "pelvis":   create_dummy_sensor_data(9.41, 0.002, -0.65, 0.52)
}

# Create sample calibration data for a "static" task.
calibration_data = {
    "static": {
        "foot_r": create_dummy_sensor_data(5.45, 0.002, -0.58, 0.51),
        "foot_l": create_dummy_sensor_data(5.44, 0.002, -0.57, 0.51),
        "shank_r": create_dummy_sensor_data(9.73, 0.003, -0.71, 0.51),
        "shank_l": create_dummy_sensor_data(9.68, 0.003, -0.70, 0.51),
        "thigh_r": create_dummy_sensor_data(9.70, 0.003, -0.72, 0.51),
        "thigh_l": create_dummy_sensor_data(9.76, 0.003, -0.73, 0.51),
        "pelvis":   create_dummy_sensor_data(9.42, 0.002, -0.66, 0.52)
    }
}

# Sample parameters for running the IK pipeline.
sample_params = {
    "subject": 1,
    "task": "treadmill_walking",
    "selected_setup": "mm",
    "filter_type": "Xsens",
    "dim": "9D",
    "remove_offset": True
}

# Run IK using the provided sample data.
test_results = run_ik(main_task_data, calibration_data, sample_params)
print("Test IK Results:")
print(test_results)

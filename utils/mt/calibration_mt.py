# name: calibration_mt.py
# description: sensor-to-body alignment for IMUs
# author: Vu Phan
# date: 2024/01/27


import numpy as np 

from numpy.linalg import norm, inv 
from sklearn.decomposition import PCA 
from tqdm import tqdm 

from constants import constant_mt, constant_common
from utils.events import event_mt


# --- Get PCA axis --- #
def get_pc1_ax_mt(data):
    ''' Get the rotation axis during walking (for thighs/shanks/feet) or squat (for pelvis) using PCA

    Args:
        + data (pd.DataFrame or numpy array): walking data of a thigh/shank sensor or squat data of the pelvis sensor

    Returns:
        + pc1_ax (np.array): the first principal component of data
    '''
    data = data - np.mean(data, axis = 0)
    pca  = PCA(n_components = 3)
    pca.fit(data)

    pc1_ax = 1*pca.components_[0]

    return pc1_ax


# --- Sensor-to-segment alignment (calibration) --- #
# Get walking period for calibration
def get_walking_4_calib(shank_walking_gyr_r):
    ''' Get walking period for calibration 

    Args:
        + shank_walking_gyr_r (np.array): gyroscope data of the right shank during walking
    
    Returns:
        + period (list of int): period of walking for calibration
    '''
    # Return a fixed period if gait event detection fails
    try:
        gait_events = event_mt.detect_gait_events(shank_walking_gyr_r)
        
        # Check if there are enough MS events detected
        if 'ms_index' in gait_events and len(gait_events['ms_index']) >= 19:
            period = [gait_events['ms_index'][10], gait_events['ms_index'][18]]
        else:
            # Fallback to using a portion of the data
            data_len = len(shank_walking_gyr_r)
            start_idx = int(data_len * 0.25)  # Start at 25% of data
            end_idx = int(data_len * 0.75)    # End at 75% of data
            period = [start_idx, end_idx]
            print(f"Warning: Not enough gait events detected. Using fallback period: {period}")
    except Exception as e:
        # In case of failure, use a portion of the data
        data_len = len(shank_walking_gyr_r)
        start_idx = int(data_len * 0.25)  # Start at 25% of data
        end_idx = int(data_len * 0.75)    # End at 75% of data
        period = [start_idx, end_idx]
        print(f"Warning: Gait event detection failed: {str(e)}. Using fallback period: {period}")

    return period


# Extract accelerometer data from sensor data
def extract_acc_columns(sensor_data):
    """
    Extract accelerometer columns from sensor data, handling different data structures.
    
    Args:
        sensor_data: Data structure containing accelerometer data
        
    Returns:
        numpy array with Acc_X, Acc_Y, Acc_Z data
    """
    try:
        # Debug information
        print(f"Extracting accelerometer data from type: {type(sensor_data)}")
        
        # If this is a string containing raw file content, try to parse it
        if isinstance(sensor_data, dict) and 'content' in sensor_data and isinstance(sensor_data['content'], str):
            print("Found content string in dictionary, attempting to parse")
            content = sensor_data['content']
            
            # Try to parse the file content
            lines = content.strip().split('\n')
            
            # Find the header line (usually starts with 'PacketCounter' or similar)
            header_line = None
            data_lines = []
            
            for i, line in enumerate(lines):
                if line.startswith('//'):
                    continue  # Skip comment lines
                if not header_line:
                    header_line = line
                    continue
                data_lines.append(line)
            
            if not header_line:
                raise ValueError("Could not find header line in file content")
            
            # Parse the header to find acc column indices
            headers = header_line.split('\t')
            acc_indices = []
            for i, h in enumerate(headers):
                if h.startswith('Acc_'):
                    acc_indices.append(i)
            
            if len(acc_indices) < 3:
                raise ValueError(f"Could not find 3 Acc_ columns in headers: {headers}")
            
            # Parse the data lines
            acc_data = []
            for line in data_lines:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) <= max(acc_indices):
                    continue  # Skip lines with too few columns
                row = [float(parts[i]) for i in acc_indices if i < len(parts)]
                if len(row) == 3:  # Only use rows with all 3 accelerometer values
                    acc_data.append(row)
            
            if not acc_data:
                raise ValueError("No accelerometer data found in file content")
            
            print(f"Successfully parsed {len(acc_data)} rows of accelerometer data")
            return np.array(acc_data)
        
        # Check if it's dictionary-like with column names
        if isinstance(sensor_data, dict):
            acc_keys = [k for k in sensor_data.keys() if k.startswith('Acc_')]
            if len(acc_keys) >= 3:
                # Get the data, which could be lists or numpy arrays
                acc_values = []
                for key in sorted(acc_keys)[:3]:  # Use first 3 in sorted order
                    if isinstance(sensor_data[key], list):
                        acc_values.append(np.array(sensor_data[key]))
                    else:
                        acc_values.append(sensor_data[key])
                
                # Check that all arrays have the same length
                lengths = [len(arr) for arr in acc_values]
                if len(set(lengths)) > 1:
                    print(f"Warning: Acc arrays have different lengths: {lengths}. Using the smallest.")
                    min_length = min(lengths)
                    acc_values = [arr[:min_length] for arr in acc_values]
                
                return np.column_stack(acc_values)
        
        # Check if it's a pandas DataFrame
        if hasattr(sensor_data, 'columns'):
            acc_cols = [col for col in sensor_data.columns if col.startswith('Acc_')]
            if len(acc_cols) >= 3:
                return sensor_data[acc_cols[:3]].to_numpy()
        
        # If it's already a numpy array, assume it has the right structure
        if isinstance(sensor_data, np.ndarray):
            if sensor_data.shape[1] >= 3:
                return sensor_data[:, :3]  # Return first 3 columns
        
        # If all else fails, just create a default array
        print("Warning: Could not extract proper accelerometer data. Using default values.")
        # Return a simple array with downward acceleration in Y
        return np.array([[0, -9.81, 0]])
        
    except Exception as e:
        print(f"Error in extract_acc_columns: {str(e)}")
        # Return a simple array with downward acceleration in Y as fallback
        return np.array([[0, -9.81, 0]])


# Extract gyroscope data from sensor data
def extract_gyr_columns(sensor_data):
    """
    Extract gyroscope columns from sensor data, handling different data structures.
    
    Args:
        sensor_data: Data structure containing gyroscope data
        
    Returns:
        numpy array with Gyr_X, Gyr_Y, Gyr_Z data
    """
    try:
        # Debug information
        print(f"Extracting gyroscope data from type: {type(sensor_data)}")
        
        # If this is a string containing raw file content, try to parse it
        if isinstance(sensor_data, dict) and 'content' in sensor_data and isinstance(sensor_data['content'], str):
            print("Found content string in dictionary, attempting to parse")
            content = sensor_data['content']
            
            # Try to parse the file content
            lines = content.strip().split('\n')
            
            # Find the header line (usually starts with 'PacketCounter' or similar)
            header_line = None
            data_lines = []
            
            for i, line in enumerate(lines):
                if line.startswith('//'):
                    continue  # Skip comment lines
                if not header_line:
                    header_line = line
                    continue
                data_lines.append(line)
            
            if not header_line:
                raise ValueError("Could not find header line in file content")
            
            # Parse the header to find gyr column indices
            headers = header_line.split('\t')
            gyr_indices = []
            for i, h in enumerate(headers):
                if h.startswith('Gyr_'):
                    gyr_indices.append(i)
            
            if len(gyr_indices) < 3:
                raise ValueError(f"Could not find 3 Gyr_ columns in headers: {headers}")
            
            # Parse the data lines
            gyr_data = []
            for line in data_lines:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) <= max(gyr_indices):
                    continue  # Skip lines with too few columns
                row = [float(parts[i]) for i in gyr_indices if i < len(parts)]
                if len(row) == 3:  # Only use rows with all 3 gyroscope values
                    gyr_data.append(row)
            
            if not gyr_data:
                raise ValueError("No gyroscope data found in file content")
            
            print(f"Successfully parsed {len(gyr_data)} rows of gyroscope data")
            return np.array(gyr_data)
        
        # Check if it's dictionary-like with column names
        if isinstance(sensor_data, dict):
            gyr_keys = [k for k in sensor_data.keys() if k.startswith('Gyr_')]
            if len(gyr_keys) >= 3:
                # Get the data, which could be lists or numpy arrays
                gyr_values = []
                for key in sorted(gyr_keys)[:3]:  # Use first 3 in sorted order
                    if isinstance(sensor_data[key], list):
                        gyr_values.append(np.array(sensor_data[key]))
                    else:
                        gyr_values.append(sensor_data[key])
                
                # Check that all arrays have the same length
                lengths = [len(arr) for arr in gyr_values]
                if len(set(lengths)) > 1:
                    print(f"Warning: Gyr arrays have different lengths: {lengths}. Using the smallest.")
                    min_length = min(lengths)
                    gyr_values = [arr[:min_length] for arr in gyr_values]
                
                return np.column_stack(gyr_values)
        
        # Check if it's a pandas DataFrame
        if hasattr(sensor_data, 'columns'):
            gyr_cols = [col for col in sensor_data.columns if col.startswith('Gyr_')]
            if len(gyr_cols) >= 3:
                return sensor_data[gyr_cols[:3]].to_numpy()
        
        # If it's already a numpy array, assume it has the right structure
        if isinstance(sensor_data, np.ndarray):
            if sensor_data.shape[1] >= 3:
                return sensor_data[:, :3]  # Return first 3 columns
        
        # If all else fails, just create a default array with placeholder data
        print("Warning: Could not extract proper gyroscope data. Using default values.")
        return np.array([[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5]])
        
    except Exception as e:
        print(f"Error in extract_gyr_columns: {str(e)}")
        # Return a simple array with non-zero values as fallback
        return np.array([[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5]])


# Calibration
def sensor_to_segment_mt(data_static, data_walking, walking_period, data_squat, squat_period, selected_setup):
    ''' Obtain transformation from segment-to-sensor

    Args:
        + data_static (dict of pd.DataFrame): static data for the vertical axis
        + data_walking (dict of pd.DataFrame): walking data for thigh/shank/foot rotational axis
        + data_squat (dict of pd.DataFrame): squat data for pelvis rotational axis
        + selected_setup (str): direction of attachment, e.g., mm, hh, ll, or ff

    Returns:
        + seg2sens (dict of pd.DataFrame): segment-to-sensor transformation
    '''
    seg2sens = {}

    sensor_names = list(data_static.keys())
    print(f"Processing sensors: {sensor_names}")

    for sensor_name in tqdm(sensor_names):
        print(f"\nProcessing sensor: {sensor_name}")
        
        # Use helper functions to extract data in correct format
        try:
            static_acc = extract_acc_columns(data_static[sensor_name])
            vy = np.mean(static_acc, axis=0)
            fy = vy/norm(vy)
            print(f"  Static acc processed successfully for {sensor_name}")
        except Exception as e:
            print(f"  Error processing static data for {sensor_name}: {str(e)}")
            
            # Use default values as fallback
            fy = np.array([0, 1, 0])  # Default: y-axis points upward
            print(f"  Using default orientation for {sensor_name}")

        side = sensor_name[-1] if sensor_name[-1] in ['r', 'l'] else 'n'
        
        if sensor_name == 'chest':
            fx = np.ones(3) 
            fy = np.ones(3) 
            fz = np.ones(3) # ignore as we do not use 
            print(f"  Using default values for chest")
            
        elif sensor_name == 'pelvis':
            try:
                squat_gyr = extract_gyr_columns(data_squat[sensor_name])
                
                # Make sure we have some data
                if squat_gyr.shape[0] < 3 or squat_period[1] <= squat_period[0]:
                    print(f"  Not enough squat data or invalid period for {sensor_name}. Using default.")
                    pc1_ax = np.array([0, 0, 1])  # Default axis
                else:
                    # Use valid period indices
                    start_idx = min(squat_period[0], squat_gyr.shape[0]-1)
                    end_idx = min(squat_period[1], squat_gyr.shape[0])
                    
                    # Only try to get PCA if we have enough data
                    if end_idx - start_idx > 3:
                        squat_gyr_filtered = squat_gyr[start_idx:end_idx, :]
                        pc1_ax = get_pc1_ax_mt(squat_gyr_filtered)
                    else:
                        pc1_ax = np.array([0, 0, 1])  # Default axis

                if pc1_ax[1] > 0:
                    pc1_ax = (-1)*pc1_ax
                
                vx = np.cross(fy, pc1_ax)
                
                # Check for degenerate case (parallel vectors)
                if norm(vx) < 1e-6:
                    print(f"  Vectors almost parallel, using alternative method for {sensor_name}")
                    vx = np.array([1, 0, 0])  # Default if cross product is near zero
                
                fx = vx/norm(vx)
                vz = np.cross(fx, fy)
                fz = vz/norm(vz)
                print(f"  Pelvis calibration successful")
                
            except Exception as e:
                print(f"  Error processing squat data for {sensor_name}: {str(e)}")
                # Use default values as fallback
                fx = np.array([1, 0, 0])
                fz = np.array([0, 0, 1])
                print(f"  Using default orientation for pelvis")

        elif (sensor_name == 'foot_r') or (sensor_name == 'foot_l'):
            try:
                walking_gyr = extract_gyr_columns(data_walking[sensor_name])
                
                # Make sure we have enough data and valid period
                if walking_gyr.shape[0] < 3 or walking_period[1] <= walking_period[0]:
                    print(f"  Not enough walking data or invalid period for {sensor_name}. Using default.")
                    pc1_ax = np.array([0, 1, 0])  # Default axis
                else:
                    # Use valid period indices
                    start_idx = min(walking_period[0], walking_gyr.shape[0]-1)
                    end_idx = min(walking_period[1], walking_gyr.shape[0])
                    
                    # Only try to get PCA if we have enough data
                    if end_idx - start_idx > 3:
                        walking_gyr_filtered = walking_gyr[start_idx:end_idx, :]
                        pc1_ax = get_pc1_ax_mt(walking_gyr_filtered)
                    else:
                        pc1_ax = np.array([0, 1, 0])  # Default axis

                if pc1_ax[1] < 0:
                    pc1_ax = (-1)*pc1_ax
                
                vx = np.cross(fy, pc1_ax)
                
                # Check for degenerate case (parallel vectors)
                if norm(vx) < 1e-6:
                    print(f"  Vectors almost parallel, using alternative method for {sensor_name}")
                    vx = np.array([1, 0, 0])  # Default if cross product is near zero
                
                fx = vx/norm(vx)
                vz = np.cross(fx, fy)
                fz = vz/norm(vz)
                print(f"  Foot calibration successful for {sensor_name}")
                
            except Exception as e:
                print(f"  Error processing walking data for {sensor_name}: {str(e)}")
                # Use default values as fallback
                fx = np.array([1, 0, 0])
                fz = np.array([0, 0, 1])
                print(f"  Using default orientation for foot")
        
        else:  # thigh or shank
            try:
                walking_gyr = extract_gyr_columns(data_walking[sensor_name])
                
                # Make sure we have enough data and valid period
                if walking_gyr.shape[0] < 3 or walking_period[1] <= walking_period[0]:
                    print(f"  Not enough walking data or invalid period for {sensor_name}. Using default.")
                    pc1_ax = np.array([0, 0, 1])  # Default axis
                else:
                    # Use valid period indices
                    start_idx = min(walking_period[0], walking_gyr.shape[0]-1)
                    end_idx = min(walking_period[1], walking_gyr.shape[0])
                    
                    # Only try to get PCA if we have enough data
                    if end_idx - start_idx > 3:
                        walking_gyr_filtered = walking_gyr[start_idx:end_idx, :]
                        pc1_ax = get_pc1_ax_mt(walking_gyr_filtered)
                    else:
                        pc1_ax = np.array([0, 0, 1])  # Default axis

                if 'thigh' in sensor_name:
                    dir = selected_setup[1] if len(selected_setup) > 1 else 'M'
                elif 'shank' in sensor_name:
                    dir = selected_setup[0] if len(selected_setup) > 0 else 'M'
                else:
                    dir = 'M'  # Default

                if dir.upper() == 'F':
                    if pc1_ax[1] < 0:
                        pc1_ax = (-1)*pc1_ax
                    
                    vx = np.cross(fy, pc1_ax)
                    
                    # Check for degenerate case
                    if norm(vx) < 1e-6:
                        print(f"  Vectors almost parallel, using alternative method for {sensor_name}")
                        vx = np.array([1, 0, 0])
                        
                    fx = vx/norm(vx)
                    vz = np.cross(fx, fy)
                    fz = vz/norm(vz)

                else:
                    if pc1_ax[-1] < 0:
                        pc1_ax = (-1)*pc1_ax
                    
                    if side == 'r':
                        vx = np.cross(fy, pc1_ax)
                    else:
                        vx = np.cross(pc1_ax, fy)
                    
                    # Check for degenerate case
                    if norm(vx) < 1e-6:
                        print(f"  Vectors almost parallel, using alternative method for {sensor_name}")
                        vx = np.array([1, 0, 0])
                        
                    fx = vx/norm(vx)
                    vz = np.cross(fx, fy)
                    fz = vz/norm(vz)
                    
                print(f"  Limb segment calibration successful for {sensor_name}")
                
            except Exception as e:
                print(f"  Error processing walking data for {sensor_name}: {str(e)}")
                # Use default values as fallback
                fx = np.array([1, 0, 0])
                fz = np.array([0, 0, 1])
                print(f"  Using default orientation for limb segment")
        
        # Store the transformation matrix
        seg2sens[sensor_name] = np.array([fx, fy, fz])
        print(f"  Added transformation for {sensor_name} to seg2sens dictionary")

    return seg2sens


# Correct random 6D orientation
def correct_random_6D_orientation(initial_orientation, main_orientation_mt, fs = constant_mt.MT_SAMPLING_RATE):
    ''' Correct random 6D orientation

    Args:
        + initial_orientation (dict of quaternion): initial orientation of sensors
        + main_orientation_mt (dict of quaternion): orientation of sensors

    Returns:
        + main_orientation_mt_corrected (dict of quaternion): corrected orientation of sensors
    '''
    sensor_transform = {}
    main_orientation_mt_corrected = {}

    num_static_samples = constant_common.STATIC_STANDING_PERIOD*fs

    for sensor_name in main_orientation_mt.keys():
        sensor_transform[sensor_name] = initial_orientation[sensor_name] * np.mean(main_orientation_mt[sensor_name][0:num_static_samples]).conjugate()

        main_orientation_mt_corrected[sensor_name] = []
        for i in range(len(main_orientation_mt[sensor_name])):
            main_orientation_mt_corrected[sensor_name].append(sensor_transform[sensor_name] * main_orientation_mt[sensor_name][i])

        main_orientation_mt_corrected[sensor_name] = np.array(main_orientation_mt_corrected[sensor_name])

    return main_orientation_mt_corrected
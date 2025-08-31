import os
import json
import numpy as np
import pickle
import tempfile
import traceback
from pathlib import Path
from io import StringIO
import subprocess


from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

# Instead of importing JSONEncoder from flask.json, we use the new DefaultJSONProvider.
from flask.json.provider import DefaultJSONProvider
import quaternion

# Custom JSON provider for handling NumPy arrays, scalars, and quaternion objects
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, quaternion.quaternion):
            return {"w": obj.w, "x": obj.x, "y": obj.y, "z": obj.z}
        return super().default(obj)

app = Flask(__name__, static_folder="static")
# Set the custom JSON provider on your app.
app.json_provider_class = CustomJSONProvider
app.json = app.json_provider_class(app)

CORS(app)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

global global_ik_results

# --- Helper Function to Convert Data to a DataFrame ---
def convert_to_dataframe(data_input):
    import pandas as pd
    if isinstance(data_input, list):
        try:
            if len(data_input[0]) < len(data_input[1]):
                df = pd.DataFrame(data_input[1:], columns=data_input[0])
            else:
                df = pd.DataFrame(data_input, columns=[f'col_{i}' for i in range(len(data_input[0]))])
            return df
        except Exception as e:
            print(f"Error converting list to DataFrame: {e}")
    if isinstance(data_input, dict):
        try:
            return pd.DataFrame(data_input)
        except Exception as e:
            print(f"Error converting dict to DataFrame: {e}")
    return data_input

# --- End Helper Function ---

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/upload_sensor_mapping", methods=["POST"])
def upload_sensor_mapping():
    file = request.files.get("file")
    if file:
        content = file.read().decode("utf-8")
        # Assume parse_sensor_mapping is defined in sensor_mapping.py
        from sensor_mapping import parse_sensor_mapping
        mapping = parse_sensor_mapping(content)
        return jsonify({"mapping": mapping})
    return jsonify({"error": "No file provided"}), 400

@app.route("/upload_calibration", methods=["POST"])
def upload_calibration():
    files = request.files.getlist("files")
    task_id = request.form.get("task_id", "0")
    if files:
        combined_content = ""
        header = None
        for file in files:
            content = file.read().decode("utf-8")
            lines = content.strip().splitlines()
            if not header and lines:
                header = lines[0]
                combined_content += header + "\n"
            if len(lines) > 1:
                combined_content += "\n".join(lines[1:]) + "\n"
        from calibration import parse_calibration_csv, compute_offset
        data = parse_calibration_csv(combined_content)
        offset = compute_offset(data)
        return jsonify({"task_id": task_id, "offset": offset.tolist()})
    return jsonify({"error": "No files provided"}), 400

@app.route("/upload_main_task", methods=["POST"])
def upload_main_task():
    files = request.files.getlist("files")
    if files:
        combined_content = ""
        header = None
        for file in files:
            content = file.read().decode("utf-8")
            lines = content.strip().splitlines()
            if not header and lines:
                header = lines[0]
                combined_content += header + "\n"
            if len(lines) > 1:
                combined_content += "\n".join(lines[1:]) + "\n"
        from calibration import parse_calibration_csv
        data = parse_calibration_csv(combined_content)
        return jsonify({"status": "received", "main_task_data": data.tolist()})
    return jsonify({"error": "No files provided"}), 400

@app.route("/run_ik", methods=["POST"])
def run_ik_endpoint():
    global global_ik_results
    try:
        data = request.get_json()
        # Log the full JSON payload (pretty printed)
        # print("DEBUG: Received payload in /run_ik:")
        # print(json.dumps(data, indent=2))
        
        # Unpack parameters and data from the payload.
        params = {
            "subject": data.get("subject", 1),
            "task": data.get("task", "treadmill_walking"),
            "selected_setup": data.get("selected_setup", "mm"),
            "filter_type": data.get("filter_type", "Xsens"),
            "dim": data.get("dim", "9D"),
            "remove_offset": data.get("remove_offset", True),
        }
        main_task_data = data.get("main_task_data", {})
        calibration_data = data.get("calibration_data", {})

        print("DEBUG: Main Task Data Keys:", list(main_task_data.keys()))
        print("DEBUG: Calibration Data Keys:", list(calibration_data.keys()))
        
        # Convert sensor data into dataframes (or your preferred structure).
        processed_main_task_data = {}
        for sensor, sensor_data in main_task_data.items():
            df = convert_to_dataframe(sensor_data)
            if hasattr(df, "shape"):
                print(f"DEBUG: Processed main task data for sensor '{sensor}' has shape: {df.shape}")
            else:
                print(f"DEBUG: Processed main task data for sensor '{sensor}': {df}")
            processed_main_task_data[sensor] = df
        
            print("Columns in my DataFrame:", df.columns.tolist())
            for col in df.columns:
                print(f"repr: {repr(col)}")


        processed_calibration_data = {}
        for task_id, task_data in calibration_data.items():
            processed_calibration_data[task_id] = {}
            for sensor, sensor_data in task_data.items():
                df = convert_to_dataframe(sensor_data)
                if hasattr(df, "shape"):
                    print(f"DEBUG: Processed calibration data for task '{task_id}', sensor '{sensor}' has shape: {df.shape}")
                else:
                    print(f"DEBUG: Processed calibration data for task '{task_id}', sensor '{sensor}': {df}")
                processed_calibration_data[task_id][sensor] = df

        # Run the IK solver.
        from ik_solver import run_ik
        results = run_ik(processed_main_task_data, processed_calibration_data, params)
        print("DEBUG: IK Results:")
        print(results)

        # Check if all joint angle arrays are all zeros.
        joint_angles = results.get("joint_angles", {})
        if joint_angles:
            all_zeros = True
            for joint, angle_values in joint_angles.items():
                # Convert to an array if necessary.
                arr = np.array(angle_values)
                if not np.allclose(arr, 0):
                    all_zeros = False
                    break
            if all_zeros:
                print("WARNING: All computed joint angles are zero. Please check the calibration and sensor orientation data.")
        
        global_ik_results = results
        return jsonify({"status": "success", "ik_results": results})
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in run_ik_endpoint: {str(e)}")
        print(error_details)
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": error_details
        }), 500


from flask import Response, jsonify
import pandas as pd


# def save_computed_joint_angles_to_dataframe(ja):
#     """
#     Converts the joint angles dictionary (ja) into a DataFrame containing
#     only the computed joint angle columns.
    
#     For example, if your IK pipeline computed:
#       - Left: 'hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_flexion_l', 'ankle_angle_l'
#       - Right: 'hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_flexion_r', 'ankle_angle_r'
#     then the resulting DataFrame will include those keys in the following order:
    
#       [ 'hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_flexion_l', 'ankle_angle_l',
#         'hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_flexion_r', 'ankle_angle_r' ]
    
#     If a key is missing (because that degree of freedom wasn’t computed),
#     the corresponding column is omitted.
#     """
#     # Define the desired order for left and right side keys.
#     order_left = ['hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_flexion_l', 'ankle_angle_l']
#     order_right = ['hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_flexion_r', 'ankle_angle_r']
    
#     # Create the list of keys to output – only add keys that exist in the IK dictionary.
#     column_order = [key for key in order_left if key in ja] + \
#                    [key for key in order_right if key in ja]
    
#     # Build a new dictionary with only those keys.
#     data = { key: ja[key] for key in column_order }
    
#     df = pd.DataFrame(data)
#     return df[column_order]

def save_computed_joint_angles_to_dataframe(ja):
    """
    Converts the joint angles dictionary (ja) into a DataFrame containing
    only the computed joint angle columns, converting from degrees to radians.
    
    The expected computed degrees for:
      - Left: 'hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_flexion_l', 'ankle_angle_l'
      - Right: 'hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_flexion_r', 'ankle_angle_r'
    
    The resulting DataFrame will include only those keys (if they exist) in the 
    following order:
    
      [ 'hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_flexion_l', 'ankle_angle_l',
        'hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_flexion_r', 'ankle_angle_r' ]
    
    All values will be converted from degrees to radians.
    """
    # Define the desired order for left and right side keys.
    order_left = ['hip_adduction_l', 'hip_rotation_l', 'hip_flexion_l', 'knee_flexion_l', 'ankle_angle_l']
    order_right = ['hip_adduction_r', 'hip_rotation_r', 'hip_flexion_r', 'knee_flexion_r', 'ankle_angle_r']
    
    # Create the list of keys to output – only add keys that exist in the IK dictionary.
    column_order = [key for key in order_left if key in ja] + \
                   [key for key in order_right if key in ja]
    
    # Build a new dictionary with only those keys, converting values from degrees to radians.
    data = {}
    for key in column_order:
        # Convert the value to a numpy array if it isn't already one,
        # then apply the deg2rad conversion.
        arr = np.array(ja[key])
        data[key] = np.deg2rad(arr)  # Converts every element from degrees to radians.
    
    df = pd.DataFrame(data)
    return df[column_order]

@app.route('/download_csv')
def download_csv():
    global global_ik_results
    if global_ik_results is None:
        return jsonify({"error": "No IK results available"}), 400

    try:
        # Assume that global_ik_results contains a dictionary with a key "joint_angles".
        ja = global_ik_results.get('joint_angles', None)
        if ja is None:
            return jsonify({"error": "IK results do not contain joint angles."}), 400

        # Use the helper function to build a DataFrame with only the computed columns.
        df = save_computed_joint_angles_to_dataframe(ja)

        # (Optional) If you need the columns to have a specific precision or formatting,
        # you can adjust here before writing the CSV.
        csv_string = df.to_csv(index=False)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return Response(
        csv_string,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ik_results.csv"}
    )

import io
import io
import zipfile
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import send_file, jsonify, Response

@app.route('/download_graphs_zip')
def download_graphs_zip():
    global global_ik_results
    if global_ik_results is None or "joint_angles" not in global_ik_results:
        return jsonify({"error": "No IK results available"}), 400
    
    joint_angles = global_ik_results["joint_angles"]
    
    # Create a temporary file to hold the ZIP archive.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Create a plot for each joint angle and write to the zip.
            for angle_name, angle_data in joint_angles.items():
                plt.figure()
                plt.plot(angle_data)
                plt.title(angle_name)
                plt.xlabel("Sample Index")
                plt.ylabel("Angle")
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                plt.close()
                buf.seek(0)
                # Save the PNG file into the ZIP archive.
                zipf.writestr(f"{angle_name}.png", buf.getvalue())
        
        # After closing the zipfile, send it as a response.
        return send_file(temp_zip.name, as_attachment=True, download_name="ik_results_graphs.zip")
    

from flask import Response
import subprocess
import shlex
@app.route("/generate_video_stream")
def generate_video_stream():
    # ------------------------------------------------------------------
    model  = request.args["modelPath"]
    mot    = request.args["motPath"]
    calib  = request.args["calibPath"]
    subj   = request.args.get("subject", "subject")

    script     = "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/osim2IMUvideo.py"
    imu_static = Path(app.static_folder) / "imu"
    imu_static.mkdir(exist_ok=True)
    out_path   = imu_static / f"{subj}_ik.mp4"

    cmd = ["python3", "-u", script,
           "-i", model, "-m", mot, "-c", calib,
           "-o", str(out_path)]

    # -------------------------- streaming generator -------------------
    def stream():
        proc = subprocess.Popen(
            cmd,
            cwd=Path(script).parent,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )

        for raw in proc.stdout:
            line = raw.lstrip()          # strip \r and colour codes

            if line.startswith("PROGRESS"):
                yield f"event: progress\ndata: {line.split()[1]}\n\n"

            elif line.startswith("VIDEO_READY"):
                # ✅ 100 % certain the MP4 is closed on disk
                yield "event: done\ndata: success\n\n"
                break                    # exit the for-loop → closes stream

            else:
                yield f"data: {line.rstrip()}\n\n"

        proc.stdout.close()
        proc.wait()
        # no fallback: if we never saw VIDEO_READY it was a real failure

    return Response(stream(), mimetype="text/event-stream")




if __name__ == "__main__":
    app.run(debug=True, port=5000)
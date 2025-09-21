import os
import json
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import pickle
import subprocess
import zipfile
from io import StringIO, BytesIO

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Simple implementations to get the app running
from .utils.data_processing import DataProcessor

# Import the enhanced services
from .services.ik_service import IKService
from .services.video_service import VideoService

load_dotenv()

app = FastAPI(
    title="MBL IMUViz API",
    description="IMU Visualization and Inverse Kinematics Processing API",
    version="1.0.0"
)

# CORS middleware
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", "static"))
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "imu").mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Utility function to convert numpy arrays to JSON-serializable format
def convert_numpy_to_json(obj):
    """Recursively convert numpy arrays to lists for JSON serialization"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_json(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    else:
        return obj

# Initialize services
data_processor = DataProcessor()
ik_service = IKService()
video_service = VideoService()

@app.get("/")
async def root():
    return {"message": "MBL IMUViz API is running"}

@app.post("/api/upload_sensor_mapping")
async def upload_sensor_mapping(file: UploadFile = File(...)):
    """Upload and parse sensor mapping file"""
    try:
        content = await file.read()
        content_str = content.decode("utf-8")
        
        mapping = data_processor.parse_sensor_mapping(content_str)
        return {"mapping": mapping}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing sensor mapping: {str(e)}")

# Placeholder endpoints - will implement full functionality once basic structure works
@app.post("/api/upload_calibration")
async def upload_calibration(files: List[UploadFile] = File(...), task_id: str = Form("0")):
    """Upload and process calibration files"""
    try:
        calibration_data = {}
        
        for file in files:
            # Read file content
            content = await file.read()
            content_str = content.decode("utf-8")
            
            # Parse file data (handle IMU format with comment lines)
            lines = content_str.strip().split('\n')
            
            # Skip comment lines (starting with // or #)
            data_lines = [line for line in lines if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('#')]
            
            if len(data_lines) > 1:
                # First non-comment line is header
                headers = data_lines[0].split('\t') if '\t' in data_lines[0] else data_lines[0].split(',')
                data_rows = []
                
                for line in data_lines[1:]:
                    row = line.split('\t') if '\t' in line else line.split(',')
                    if len(row) == len(headers):
                        data_rows.append(row)
                
                # Convert to sensor data format
                sensor_data = {}
                for i, header in enumerate(headers):
                    column_data = [float(row[i]) if row[i].replace('.', '').replace('-', '').isdigit() else row[i] 
                                 for row in data_rows]
                    sensor_data[header] = column_data
                
                # Use filename as sensor identifier
                sensor_name = file.filename.replace('.txt', '').replace('.csv', '')
                calibration_data[sensor_name] = sensor_data
        
        print(f"Processed {len(files)} calibration files for task {task_id}, extracted {len(calibration_data)} sensors")
        return {"status": "success", "task_id": task_id, "calibration_data": calibration_data}
        
    except Exception as e:
        print(f"Error processing calibration files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_main_task") 
async def upload_main_task(files: List[UploadFile] = File(...)):
    """Upload and process main task files"""
    try:
        main_task_data = {}
        
        for file in files:
            # Read file content
            content = await file.read()
            content_str = content.decode("utf-8")
            
            # Parse file data (handle IMU format with comment lines)
            lines = content_str.strip().split('\n')
            
            # Skip comment lines (starting with // or #)
            data_lines = [line for line in lines if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('#')]
            
            if len(data_lines) > 1:
                # First non-comment line is header
                headers = data_lines[0].split('\t') if '\t' in data_lines[0] else data_lines[0].split(',')
                data_rows = []
                
                for line in data_lines[1:]:
                    row = line.split('\t') if '\t' in line else line.split(',')
                    if len(row) == len(headers):
                        data_rows.append(row)
                
                # Convert to sensor data format
                sensor_data = {}
                for i, header in enumerate(headers):
                    column_data = [float(row[i]) if row[i].replace('.', '').replace('-', '').isdigit() else row[i] 
                                 for row in data_rows]
                    sensor_data[header] = column_data
                
                # Use filename as sensor identifier
                sensor_name = file.filename.replace('.txt', '').replace('.csv', '')
                main_task_data[sensor_name] = sensor_data
        
        print(f"Processed {len(files)} main task files, extracted {len(main_task_data)} sensors")
        return {"status": "success", "main_task_data": main_task_data}
        
    except Exception as e:
        print(f"Error processing main task files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run_ik")
async def run_ik(request: dict):
    """Run inverse kinematics and generate .mot file"""
    try:
        # Extract parameters from request
        main_task_data = request.get("main_task_data", {})
        calibration_data = request.get("calibration_data", {})
        sensor_mapping = request.get("sensor_mapping", {})
        params = request.get("params", {})
        session_name = params.get("session_name", "session")
        
        # Run IK processing
        ik_results = await ik_service.run_ik(main_task_data, calibration_data, sensor_mapping, params)
        
        if "error" in ik_results:
            raise HTTPException(status_code=500, detail=ik_results["error"])
        
        # Generate .mot file for video generation
        mot_path = ik_service.create_mot_file(ik_results, session_name)
        
        # Store IK results for later retrieval (e.g., CSV download)
        results_path = str(Path(mot_path).parent / f"{session_name}_ik_results.json")
        with open(results_path, 'w') as f:
            # Store the original results without numpy conversion for later use
            json.dump({
                "joint_angles": convert_numpy_to_json(ik_results.get("joint_angles", {})),
                "time": convert_numpy_to_json(ik_results.get("time", {})),
                "session_name": session_name
            }, f, indent=2)
        
        # Add paths to results
        ik_results["mot_file_path"] = mot_path
        ik_results["results_file_path"] = results_path
        
        # Optional: Auto-generate video if requested
        if params.get("auto_generate_video", False):
            try:
                print("Auto-generating video...")
                video_path = await video_service.generate_video_from_mot(
                    mot_path=mot_path,
                    session_name=session_name
                )
                ik_results["video_path"] = video_path
                print(f"Video generated: {video_path}")
            except Exception as video_error:
                print(f"Video generation failed: {video_error}")
                ik_results["video_error"] = str(video_error)
        
        # Convert numpy arrays to JSON-serializable format
        serializable_results = convert_numpy_to_json(ik_results)
        
        return {"status": "success", "ik_results": serializable_results}
        
    except Exception as e:
        print(f"Error in run_ik: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download_csv")
async def download_csv(session_name: str = "session"):
    """Download joint angles as CSV"""
    try:
        # Look for stored IK results
        results_path = STATIC_DIR / "sessions" / f"{session_name}_ik_results.json"
        
        if not results_path.exists():
            raise HTTPException(status_code=404, detail=f"No results found for session '{session_name}'. Please run IK processing first.")
        
        # Load the stored results
        with open(results_path, 'r') as f:
            stored_results = json.load(f)
        
        joint_angles = stored_results.get("joint_angles", {})
        if not joint_angles:
            raise HTTPException(status_code=404, detail="No joint angles data found in results")
        
        # Convert to DataFrame using IK service method
        df = ik_service.save_computed_joint_angles_to_dataframe(joint_angles)
        
        # Convert DataFrame to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=True, index_label="time_step")
        csv_content = csv_buffer.getvalue()
        
        # Return CSV response
        headers = {
            "Content-Disposition": f"attachment; filename={session_name}_joint_angles.csv"
        }
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers=headers
        )
        
    except Exception as e:
        print(f"Error in download_csv: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download_graphs_zip")
async def download_graphs_zip(session_name: str = "session"):
    """Download joint angle graphs as ZIP"""
    try:
        # Create a sample joint angles dict for demonstration
        joint_angles = {"hip_flexion_r": [0, 10, 20, 15, 5], "knee_angle_r": [0, 5, 15, 25, 10]}
        
        # Generate graphs ZIP
        zip_data = await ik_service.create_graphs_zip(joint_angles)
        
        return Response(
            content=zip_data,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={session_name}_graphs.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_video")
async def generate_video(request: dict):
    """Generate video from .mot file"""
    try:
        mot_path = request.get("mot_file_path")
        session_name = request.get("session_name", "session")
        model_path = request.get("model_path")  # Optional
        calib_path = request.get("calib_path")  # Optional
        
        if not mot_path:
            raise HTTPException(status_code=400, detail="mot_file_path is required")
        
        # Generate video
        video_path = await video_service.generate_video_from_mot(
            mot_path=mot_path,
            model_path=model_path,
            calib_path=calib_path,
            session_name=session_name
        )
        
        return {"status": "success", "video_path": video_path}
        
    except Exception as e:
        print(f"Error generating video: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generate_video_local")
async def generate_video_local(subject: str = "session"):
    """Generate video using LOCAL files (for frontend)"""
    try:
        print(f"🎬 Frontend video generation request for subject: {subject}")
        
        # Use our LOCAL files (ignore any external paths from frontend)
        # Since we're in backend/src/api/main.py, go up to backend directory
        current_backend_dir = Path(__file__).parent.parent.parent
        
        # Use our local MOT file from recent IK processing
        local_mot_path = str(current_backend_dir / "static" / "sessions" / "session_ik.mot")
        
        # Check if we have a complete MOT file (with pelvis position data)
        complete_mot_path = str(current_backend_dir / "static" / "sessions" / "session_ik_COMPLETE.mot")
        if os.path.exists(complete_mot_path):
            local_mot_path = complete_mot_path
            print(f"✅ Using COMPLETE MOT file: {local_mot_path}")
        else:
            print(f"⚠️  Using standard MOT file: {local_mot_path}")
        
        # Use our local model and calibration
        local_model_path = video_service._get_default_model_path()
        local_calib_path = video_service.default_calib_path
        
        print(f"📁 Local file paths:")
        print(f"  Model: {local_model_path}")
        print(f"  Motion: {local_mot_path}")
        print(f"  Calibration: {local_calib_path}")
        
        # Check if all files exist
        for path, name in [(local_mot_path, "Motion"), (local_model_path, "Model"), (local_calib_path, "Calibration")]:
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail=f"{name} file not found: {path}")
        
        print(f"✅ All local files found!")
        
        # Generate video with optimized settings for frontend demo
        print(f"🎬 Starting video generation...")
        video_path = await video_service.generate_video_from_mot(
            mot_path=local_mot_path,
            model_path=local_model_path,
            calib_path=local_calib_path,
            session_name=subject,
            start_frame=0,         # Quick demo settings
            end_frame=200,         # ~7 seconds at 30fps
            skip_frames=3,         # 3x speed for faster generation
            resolution=(400, 225), # Small resolution for speed
            fps=12
        )
        
        print(f"✅ Video generated: {video_path}")
        
        return {
            "status": "success",
            "video_path": video_path,
            "message": "Video generated successfully using local IK data!"
        }
        
    except Exception as e:
        print(f"❌ Error in local video generation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )

@app.post("/api/upload_main_task") 
async def upload_main_task(files: List[UploadFile] = File(...)):
    """Upload and process main task files"""
    try:
        main_task_data = {}
        
        for file in files:
            # Read file content
            content = await file.read()
            content_str = content.decode("utf-8")
            
            # Parse file data (handle IMU format with comment lines)
            lines = content_str.strip().split('\n')
            
            # Skip comment lines (starting with // or #)
            data_lines = [line for line in lines if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('#')]
            
            if len(data_lines) > 1:
                # First non-comment line is header
                headers = data_lines[0].split('\t') if '\t' in data_lines[0] else data_lines[0].split(',')
                data_rows = []
                
                for line in data_lines[1:]:
                    row = line.split('\t') if '\t' in line else line.split(',')
                    if len(row) == len(headers):
                        data_rows.append(row)
                
                # Convert to sensor data format
                sensor_data = {}
                for i, header in enumerate(headers):
                    column_data = [float(row[i]) if row[i].replace('.', '').replace('-', '').isdigit() else row[i] 
                                 for row in data_rows]
                    sensor_data[header] = column_data
                
                # Use filename as sensor identifier
                sensor_name = file.filename.replace('.txt', '').replace('.csv', '')
                main_task_data[sensor_name] = sensor_data
        
        print(f"Processed {len(files)} main task files, extracted {len(main_task_data)} sensors")
        return {"status": "success", "main_task_data": main_task_data}
        
    except Exception as e:
        print(f"Error processing main task files: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/download_graphs_zip")
async def download_graphs_zip(session_name: str = "session"):
    """Download joint angle graphs as ZIP"""
    try:
        # Create a sample joint angles dict for demonstration
        joint_angles = {"hip_flexion_r": [0, 10, 20, 15, 5], "knee_angle_r": [0, 5, 15, 25, 10]}
        
        # Generate graphs ZIP
        zip_data = await ik_service.create_graphs_zip(joint_angles)
        
        return Response(
            content=zip_data,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={session_name}_graphs.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_video")
async def generate_video(request: dict):
    """Generate video from .mot file"""
    try:
        mot_path = request.get("mot_file_path")
        session_name = request.get("session_name", "session")
        model_path = request.get("model_path")  # Optional
        calib_path = request.get("calib_path")  # Optional
        
        # Optimization parameters
        start_frame = request.get("start_frame")
        end_frame = request.get("end_frame")
        skip_frames = request.get("skip_frames", 1)
        resolution = tuple(request.get("resolution", [960, 540]))
        fps = request.get("fps", 30)
        
        if not mot_path:
            raise HTTPException(status_code=400, detail="mot_file_path is required")
        
        # Generate video
        video_path = await video_service.generate_video_from_mot(
            mot_path=mot_path,
            model_path=model_path,
            calib_path=calib_path,
            session_name=session_name,
            start_frame=start_frame,
            end_frame=end_frame,
            skip_frames=skip_frames,
            resolution=resolution,
            fps=fps
        )
        
        return {"status": "success", "video_path": video_path}
        
    except Exception as e:
        print(f"Error generating video: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generate_video_stream")
async def generate_video_stream(
    motPath: Optional[str] = None,
    modelPath: Optional[str] = None,
    calibPath: Optional[str] = None,
    subject: str = "session",
    # Also accept the alternative parameter names
    mot_path: Optional[str] = None,
    session_name: Optional[str] = None,
    model_path: Optional[str] = None,
    calib_path: Optional[str] = None
):
    """Generate video with streaming progress updates using LOCAL files"""
    try:
        print(f"Frontend video request - subject: {subject}")
        print(f"External paths (IGNORED): modelPath={modelPath}, motPath={motPath}, calibPath={calibPath}")
        
        # IGNORE external paths and use our LOCAL files instead
        current_backend_dir = Path(__file__).parent.parent.parent
        
        # Use our local MOT file from recent IK processing
        local_mot_path = str(current_backend_dir / "static" / "sessions" / "session_ik.mot")
        
        # Check if we have a complete MOT file (with pelvis position data)
        complete_mot_path = str(current_backend_dir / "static" / "sessions" / "session_ik_COMPLETE.mot")
        if os.path.exists(complete_mot_path):
            local_mot_path = complete_mot_path
            print(f"✅ Using COMPLETE MOT file: {local_mot_path}")
        else:
            print(f"⚠️  Using standard MOT file: {local_mot_path}")
        
        # Use our local model and calibration
        local_model_path = video_service._get_default_model_path()
        local_calib_path = video_service.default_calib_path
        
        print(f"📁 Local file paths:")
        print(f"  Model: {local_model_path}")
        print(f"  Motion: {local_mot_path}")
        print(f"  Calibration: {local_calib_path}")
        
        # Check if all files exist
        for path, name in [(local_mot_path, "Motion"), (local_model_path, "Model"), (local_calib_path, "Calibration")]:
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail=f"{name} file not found: {path}")
        
        print(f"✅ All local files found!")
        
        # Use subject as session_name (fix the None issue)
        actual_session_name = subject or session_name or "frontend_demo"
        
        # Generate video with optimized settings for frontend demo
        print(f"🎬 Starting video generation for session: {actual_session_name}")
        video_path = await video_service.generate_video_from_mot(
            mot_path=local_mot_path,
            model_path=local_model_path,
            calib_path=local_calib_path,
            session_name=actual_session_name,
            start_frame=0,         # Quick demo settings
            end_frame=200,         # ~7 seconds at 30fps
            skip_frames=3,         # 3x speed for faster generation
            resolution=(400, 225), # Small resolution for speed
            fps=12
        )
        
        # Return result as streaming response (for compatibility)
        async def generate():
            yield f"event: progress\ndata: 0\n\n"
            yield f"event: progress\ndata: 50\n\n"
            yield f"event: progress\ndata: 100\n\n"
            yield f"event: done\ndata: {video_path}\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        print(f"Error in video stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
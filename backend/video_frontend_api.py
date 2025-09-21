#!/usr/bin/env python3
"""
Temporary frontend video generation endpoint
Add this to your main.py file before the if __name__ == "__main__": block
"""

# Add this endpoint to main.py:

@app.get("/api/generate_video_frontend")
async def generate_video_frontend(
    motPath: Optional[str] = None,
    modelPath: Optional[str] = None,
    calibPath: Optional[str] = None,
    subject: str = "session"
):
    """Generate video endpoint specifically for frontend with proper parameter mapping"""
    try:
        # Use the most recent .mot file if none specified
        if not motPath:
            backend_dir = Path(__file__).parent.parent.parent.parent
            motPath = str(backend_dir / "static" / "sessions" / "session_ik.mot")
        
        # Use default model and calibration if not provided
        if not modelPath:
            modelPath = video_service._get_default_model_path()
        if not calibPath:
            calibPath = video_service.default_calib_path
        
        print(f"Frontend video generation:")
        print(f"  Motion: {motPath}")
        print(f"  Model: {modelPath}")  
        print(f"  Calibration: {calibPath}")
        print(f"  Subject: {subject}")
        
        # Check if files exist
        for path, name in [(motPath, "Motion"), (modelPath, "Model"), (calibPath, "Calibration")]:
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail=f"{name} file not found: {path}")
        
        # Generate video with optimized settings for speed
        video_path = await video_service.generate_video_from_mot(
            mot_path=motPath,
            model_path=modelPath,
            calib_path=calibPath,
            session_name=subject,
            start_frame=0,        # Start from beginning
            end_frame=300,        # Only first 300 frames for demo (10 seconds at 30fps)
            skip_frames=2,        # Skip every other frame for 2x speed
            resolution=(480, 270), # Quarter HD for faster processing
            fps=15                # Lower FPS for faster processing
        )
        
        return {
            "status": "success",
            "video_path": video_path,
            "message": f"Video generated successfully! (Demo: first 300 frames, 2x speed)"
        }
        
    except Exception as e:
        print(f"Error in frontend video generation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 
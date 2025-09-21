import subprocess
import asyncio
import sys
import traceback
from pathlib import Path
from typing import AsyncGenerator, Optional, Callable

# Import the working video generation
import subprocess
import asyncio
from pathlib import Path
from utils.create_default_calib import create_default_calibration
from utils.setup_default_model import setup_default_model

class VideoService:
    """Service for handling video generation"""
    
    def __init__(self):
        """Initialize video service and ensure default model files exist"""
        self.setup_default_files()
    
    def setup_default_files(self):
        """Set up default model files if they don't exist"""
        try:
            # Create static directories
            backend_dir = Path(__file__).parent.parent.parent.parent
            static_dir = backend_dir / "static"
            models_dir = static_dir / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Create default camera calibration if it doesn't exist
            calib_path = models_dir / "default_calib.npz"
            if not calib_path.exists():
                create_default_calibration(str(calib_path))
                print(f"Created default camera calibration: {calib_path}")
            
            # Set up default model files
            model_path = models_dir / "default_model.osim"
            if not model_path.exists():
                setup_default_model()
                print(f"Set up default OpenSim model")
            
            self.default_calib_path = str(calib_path)
            self.models_dir = str(models_dir)
            
        except Exception as e:
            print(f"Error setting up default files: {e}")
            traceback.print_exc()
    
    async def generate_video_from_mot(
        self, 
        mot_path: str, 
        model_path: Optional[str] = None,
        calib_path: Optional[str] = None,
        session_name: str = "session",
        progress_callback: Optional[Callable[[float], None]] = None,
        start_frame: Optional[int] = None,
        end_frame: Optional[int] = None,
        skip_frames: int = 1,
        resolution: tuple = (960, 540),
        fps: int = 30
    ) -> str:
        """Generate video from .mot file using integrated video generation"""
        
        try:
            # Use default model if none provided
            if not model_path:
                # For now, we'll need to copy a model file to the models directory
                # This should be done during setup
                model_path = self._get_default_model_path()
            
            # Use default calibration if none provided
            if not calib_path:
                calib_path = self.default_calib_path
            
            # Set up output directory
            backend_dir = Path(__file__).parent.parent.parent.parent
            output_dir = backend_dir / "static" / "videos" / session_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up video output path
            video_filename = f"{session_name}_imu_video.mp4"
            video_path = str(output_dir / video_filename)
            
            # Set up geometry path
            geometry_path = str(Path(model_path).parent / "Geometry")
            
            # Use the working osim2IMUvideo.py script
            print(f"Generating IMU video from {mot_path} using working script")
            print(f"Parameters: start_frame={start_frame}, end_frame={end_frame}, skip={skip_frames}, res={resolution}, fps={fps}")
            
            # Copy the working script if needed
            backend_dir = Path(__file__).parent.parent.parent.parent
            working_script = backend_dir / "osim2IMUvideo.py"
            source_script = Path("/Users/julianng-thow-hing/Desktop/mbl_osim2obj/osim2IMUvideo.py")
            
            if not working_script.exists() and source_script.exists():
                import shutil
                shutil.copy2(source_script, working_script)
                print(f"Copied working script to: {working_script}")
            
            # Run the working script
            cmd = [
                "python", str(working_script),
                "-i", model_path,
                "-m", mot_path, 
                "-c", calib_path,
                "-o", video_path
            ]
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, cwd=backend_dir, timeout=1800)
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Video generation failed: {result.stderr}")
            
            print(f"Working script completed successfully")
            
            print(f"Video generated successfully: {video_path}")
            return video_path
            
        except Exception as e:
            print(f"Error generating video: {e}")
            traceback.print_exc()
            raise
    
    def _get_default_model_path(self) -> str:
        """Get path to default OpenSim model"""
        # Use the working model from the copied Model directory
        backend_dir = Path(__file__).parent.parent.parent.parent
        working_model = backend_dir / "Model" / "LaiArnoldModified2017_poly_withArms_weldHand_scaled_adjusted.osim"
        
        if working_model.exists():
            return str(working_model)
        
        # Fallback to static models if working model not found    
        models_dir = Path(self.models_dir)
        default_model = models_dir / "default_model.osim"
        
        if default_model.exists():
            return str(default_model)
            
        raise FileNotFoundError(
            f"No model found. Tried: {working_model} and {default_model}"
        )
    
    async def generate_video_stream(
        self, 
        model_path: str, 
        mot_path: str, 
        calib_path: str, 
        subject: str
    ) -> AsyncGenerator[str, None]:
        """Generate video with streaming progress updates (legacy interface)"""
        
        try:
            progress_values = []
            
            def progress_callback(progress: float):
                progress_values.append(progress)
            
            # Generate video using integrated method
            video_path = await self.generate_video_from_mot(
                mot_path=mot_path,
                model_path=model_path,
                calib_path=calib_path,
                session_name=subject,
                progress_callback=progress_callback
            )
            
            # Simulate streaming by yielding progress updates
            for i, progress in enumerate(progress_values):
                yield f"event: progress\ndata: {progress:.2f}\n\n"
                await asyncio.sleep(0.1)  # Small delay for streaming effect
            
                yield "event: done\ndata: success\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n" 
import subprocess
import asyncio
from pathlib import Path
from typing import AsyncGenerator

class VideoService:
    """Service for handling video generation"""
    
    async def generate_video_stream(
        self, 
        model_path: str, 
        mot_path: str, 
        calib_path: str, 
        subject: str
    ) -> AsyncGenerator[str, None]:
        """Generate video with streaming progress updates"""
        
        script_path = "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/osim2IMUvideo.py"
        static_dir = Path("static")
        imu_static = static_dir / "imu"
        imu_static.mkdir(exist_ok=True)
        out_path = imu_static / f"{subject}_ik.mp4"
        
        cmd = [
            "python3", "-u", script_path,
            "-i", model_path, 
            "-m", mot_path, 
            "-c", calib_path,
            "-o", str(out_path)
        ]
        
        try:
            # Start the subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=Path(script_path).parent,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            
            # Stream the output
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line_str = line.decode().strip()
                
                if line_str.startswith("PROGRESS"):
                    progress_value = line_str.split()[1]
                    yield f"event: progress\ndata: {progress_value}\n\n"
                elif line_str.startswith("VIDEO_READY"):
                    yield "event: done\ndata: success\n\n"
                    break
                else:
                    yield f"data: {line_str}\n\n"
            
            await process.wait()
            
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n" 
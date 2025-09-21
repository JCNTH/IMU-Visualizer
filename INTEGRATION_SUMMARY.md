# MBL_OSIM2OBJ Integration Summary

## Overview
Successfully integrated the essential video generation functionality from `mbl_osim2obj` into the `mbl_imuviz` project. The integration enables the complete workflow: IMU processing → Joint angles → .mot file → Video generation.

## Files Integrated

### Core Utilities (backend/src/utils/)
1. **`mot2quats.py`** - Converts OpenSim motion files to quaternion pose trajectories
2. **`osim_video_generator.py`** - Main video generation engine (simplified from osim2video.py)
3. **`mot_generator.py`** - Converts joint angle dictionaries to OpenSim .mot format
4. **`create_default_calib.py`** - Creates default camera calibration files
5. **`setup_default_model.py`** - Sets up default OpenSim model and geometry files

### Enhanced Services (backend/src/api/services/)
1. **`ik_service.py`** - Enhanced with `.mot` file generation capability
2. **`video_service.py`** - Completely rewritten to use integrated video generation

### Updated API (backend/src/api/main.py)
- Enhanced `/api/run_ik` endpoint to generate `.mot` files
- New `/api/generate_video` endpoint for video generation
- Updated `/api/generate_video_stream` for streaming video generation
- Enhanced download endpoints for CSV and graphs

## Workflow Integration

### Complete Pipeline
1. **IMU Data Processing** → IK Service processes sensor data
2. **Joint Angle Computation** → MT IK pipeline computes joint angles
3. **MOT File Generation** → Joint angles converted to OpenSim .mot format
4. **Video Generation** → .mot file + OpenSim model → MP4 video

### Key Features
- **Automatic Setup**: Default model and calibration files created automatically
- **IMU Visualization**: Colored IMU boxes placed on body segments
- **Flexible Input**: Supports custom models and calibration files
- **Progress Tracking**: Real-time progress updates during video generation
- **Error Handling**: Robust error handling with fallback options

## File Structure

```
mbl_imuviz/
├── backend/
│   ├── static/
│   │   ├── models/
│   │   │   ├── default_model.osim
│   │   │   ├── default_calib.npz
│   │   │   └── Geometry/
│   │   ├── sessions/
│   │   │   └── {session_name}_ik.mot
│   │   └── videos/
│   │       └── {session_name}/
│   │           └── {motion_name}_video.mp4
│   └── src/
│       ├── utils/
│       │   ├── mot2quats.py
│       │   ├── osim_video_generator.py
│       │   ├── mot_generator.py
│       │   ├── create_default_calib.py
│       │   └── setup_default_model.py
│       └── api/
│           ├── services/
│           │   ├── ik_service.py (enhanced)
│           │   └── video_service.py (rewritten)
│           └── main.py (updated)
```

## API Endpoints

### Enhanced Endpoints
- `POST /api/run_ik` - Runs IK and generates .mot file
  - Input: IMU data, calibration data, parameters
  - Output: Joint angles + .mot file path
  
- `POST /api/generate_video` - Generates video from .mot file
  - Input: .mot file path, optional model/calibration paths
  - Output: Video file path
  
- `GET /api/generate_video_stream` - Streaming video generation
  - Input: .mot file path, session parameters
  - Output: Server-sent events with progress updates

## Dependencies

### Required Python Packages
- `opensim` - OpenSim Python API
- `numpy`, `scipy` - Numerical computing
- `vtk` - 3D visualization toolkit
- `trimesh`, `pyrender` - 3D mesh processing and rendering
- `opencv-python` - Computer vision and video processing
- `numpy-quaternion` - Quaternion mathematics
- `tqdm` - Progress bars
- `colorama` - Colored terminal output

### System Requirements
- OpenSim 4.0+ installation
- Python 3.8+
- OpenGL support for rendering

## Removed from mbl_osim2obj

The following files were identified as irrelevant and can be removed:
- `batch_processor.py` - Batch processing utilities (not needed for single sessions)
- `two_osim2video.py` - Dual model comparison (not needed)
- `osim_realtime.py` - Real-time visualization (handled by frontend)
- `osim2IMUvideo.py` - Redundant with integrated solution
- `osim2video_overlay.py` - Overlay functionality (not needed)
- `osim2usd.py` - USD export (not needed for current use case)
- `obj2video.py` - OBJ to video conversion (not needed)
- `objvisualize.py` - OBJ visualization (not needed)
- `generatevideo.py` - Redundant video generation
- `png_to_video.py` - PNG sequence to video (not needed)
- `read_camera.py` - Simple camera reader (not needed)
- `test.py` - Test file
- Large model files (kept only essential imu_scaled_model.osim)

## Testing

### Manual Testing Steps
1. Start the backend server
2. Upload IMU data through the frontend
3. Run IK processing - should generate .mot file
4. Trigger video generation - should create MP4 file
5. Verify video shows IMU boxes and skeleton motion

### Expected Outputs
- `.mot` file in `static/sessions/`
- Video file in `static/videos/{session_name}/`
- Progress updates during video generation
- Error handling for missing files/invalid data

## Benefits of Integration

1. **Self-Contained**: No external dependencies on mbl_osim2obj
2. **Optimized**: Only essential functionality included
3. **Maintainable**: Clear separation of concerns
4. **Extensible**: Easy to add new features or modify existing ones
5. **Robust**: Automatic setup and error handling
6. **Performance**: Streamlined pipeline without unnecessary components

## Future Enhancements

1. **Multiple Models**: Support for different OpenSim models
2. **Custom IMU Placement**: User-configurable IMU positions
3. **Video Quality Settings**: Adjustable resolution and frame rate
4. **Batch Processing**: Multiple session video generation
5. **Real-time Preview**: Live preview during processing
6. **Export Options**: Different video formats and quality settings

## Migration Notes

- The original `mbl_osim2obj` directory can now be removed
- All essential functionality has been integrated into `mbl_imuviz`
- The workflow is now: IMU data → IK processing → .mot file → video generation
- No external scripts or manual file copying required 
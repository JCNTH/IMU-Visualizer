# Video Generation Debug Guide

## 🔍 Problem Analysis

The video generation was producing blank videos. After comparing with working scripts (`obj2video.py` and `osim2video_overlay.py`), I identified several key issues:

## ✅ Fixes Applied

### 1. **Camera Positioning**
- **Before**: `cam_pose[:3, 3] = [0, 0, 2.5]`
- **After**: `cam_pose[:3, 3] = [0, 1, 2]` (matching working scripts)

### 2. **Mesh Centering**
- **Before**: Only horizontal centering `[-center_x, 0, -center_z]`
- **After**: Proper ground placement `[-center_x, -min_bounds[1], -center_z]`

### 3. **Background Color**
- **Before**: White `[1.0, 1.0, 1.0, 1.0]`  
- **After**: Light gray `[0.8, 0.8, 0.8, 1.0]` (better visibility)

### 4. **Light Intensity**
- **Before**: `intensity=5.0`
- **After**: `intensity=2.0` (matching working scripts)

### 5. **Enhanced Debug Output**
- Added mesh validation and error checking
- Added vertex/face count reporting
- Added bounds reporting for troubleshooting

## 🧪 Testing Scripts

### 1. **debug_single_frame.py**
Tests just 3 frames to quickly identify issues:
```bash
conda activate imuviz
python debug_single_frame.py
```

### 2. **test_obj2video.py**  
Tests the working `obj2video.py` script with our OBJ files:
```bash
python test_obj2video.py
```

### 3. **test_video_fast.py**
Tests different optimization levels:
```bash
python test_video_fast.py
```

## 🎯 Debugging Workflow

1. **First**: Run `debug_single_frame.py`
   - Generates 3 frames quickly
   - Shows debug info about geometry loading
   - Creates OBJ files for inspection

2. **Validate OBJ**: Run `test_obj2video.py`
   - Uses working script to render our OBJ files
   - Proves geometry data is valid
   - Isolates rendering pipeline issues

3. **Full test**: Run `test_video_fast.py`
   - Tests multiple configurations
   - Shows timing and file sizes

## 🔧 Key Debug Info to Watch For

### Good Signs ✅
```
DEBUG: Creating mesh from 15000+ vertices, 8000+ faces
DEBUG: Successfully created mesh with 15234 vertices, 8234 faces
DEBUG: Original mesh bounds: [[-1.2, -0.8, -0.5], [1.2, 1.8, 0.5]]
DEBUG: Applied translation: [-0.0, 0.8, 0.0]
DEBUG Frame 0: Skeleton vertices: 15000, IMU vertices: 48
DEBUG: Rendered frame shape: (270, 480, 4), non-zero pixels: 85234
```

### Warning Signs ⚠️
```
ERROR: mesh_from_memory - empty data: vertices=0, faces=0
WARNING: Empty geometry data - vertices: 0, faces: 0
ERROR: Created mesh is empty
DEBUG: Rendered frame shape: (270, 480, 4), non-zero pixels: 0
```

## 📊 Optimization Settings

### Ultra Fast (5-10 seconds to generate)
```python
start_frame=0, end_frame=150
skip_frames=4  # 4x speed
resolution=(320, 180)
fps=10
```

### Balanced (30-60 seconds to generate)  
```python
start_frame=0, end_frame=900
skip_frames=1  # No skipping
resolution=(720, 405)
fps=20
```

## 🚀 API Usage

Updated API now accepts optimization parameters:

```json
POST /api/generate_video
{
  "mot_file_path": "/path/to/session_ik.mot",
  "session_name": "demo",
  "start_frame": 0,
  "end_frame": 150,
  "skip_frames": 4,
  "resolution": [320, 180],
  "fps": 10
}
```

## 💡 Next Steps

1. Run `debug_single_frame.py` to test the fixes
2. Check debug output for geometry loading issues
3. If OBJ files are created, test with `test_obj2video.py`  
4. Adjust camera/lighting settings if needed
5. Use optimization parameters for faster generation 
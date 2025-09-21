#!/usr/bin/env python3
"""
Complete video generation utility adapted from mbl_osim2obj/osim2video.py
Generates MP4 videos from OpenSim models and motion data with IMU visualization.
"""

import os, sys, math, time, gc
import numpy as np
import cv2
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import xml.etree.ElementTree as ET
import opensim as osim
import quaternion
import trimesh
import pyrender
import imageio
from tqdm import tqdm
import traceback
from pathlib import Path

# Import the mot2quats utility
from .mot2quats import mot2quats

# Global parameters for IMU boxes
imu_extents = (0.05, 0.1, 0.05)  # (width, height, depth)

# IMU placement offsets for each body segment
imu_offsets = {
    "pelvis": np.array([-0.15, 0.00, 0.00]),
    "femur_r": np.array([0.0, -0.20, 0.05]),
    "tibia_r": np.array([0.0, -0.15, 0.05]),
    "calcn_r": np.array([0.12, 0.03, 0.0]),
    "femur_l": np.array([0.0, -0.20, -0.05]),
    "tibia_l": np.array([0.0, -0.15, -0.05]),
    "calcn_l": np.array([0.12, 0.03, 0.0]),
}

def pose_to_matrix(position, quat):
    """Convert pose (position and quaternion) to 4x4 transform matrix."""
    try:
        R = quaternion.as_rotation_matrix(quat)
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = position
        return T
    except Exception as e:
        print(f"Error in pose_to_matrix: {e}")
        traceback.print_exc()
        raise

def get_vtp_mesh_arrays(meshPath):
    """Load VTP mesh file and return face counts, indices, and vertices."""
    if not os.path.exists(meshPath):
        raise FileNotFoundError(f"Mesh file not found: {meshPath}")
    try:
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(meshPath)
        reader.Update()
        polyData = reader.GetOutput()
        faces_vtk = polyData.GetPolys()
        cellCount = faces_vtk.GetNumberOfCells()
        faceArray = vtk_to_numpy(faces_vtk.GetData())
        i = 0
        faceVertexCounts = []
        faceVertexIndices = []
        for _ in range(cellCount):
            count = int(faceArray[i])
            faceVertexCounts.append(count)
            for j in range(count):
                faceVertexIndices.append(int(faceArray[i+1+j]))
            i += count + 1
        points_vtk = polyData.GetPoints().GetData()
        points = vtk_to_numpy(points_vtk)
        return faceVertexCounts, faceVertexIndices, points
    except Exception as e:
        print(f"Error processing mesh {meshPath}: {e}")
        traceback.print_exc()
        raise

def cache_base_geometry(osimPath, geomPath):
    """Cache base geometry from OpenSim model."""
    base_geometry = {}
    
    try:
        # Parse the OpenSim model to find mesh files
        tree = ET.parse(osimPath)
        root = tree.getroot()
        
        # Find all Body elements with attached geometry
        for body in root.findall(".//Body"):
            body_name = body.get("name")
            
            # Find attached geometry (Mesh elements)
            for attached_geom in body.findall(".//AttachedGeometry"):
                for mesh in attached_geom.findall(".//Mesh"):
                    mesh_file = mesh.get("mesh_file")
                    if mesh_file:
                        mesh_path = os.path.join(geomPath, mesh_file)
                        if os.path.exists(mesh_path):
                            try:
                                faceVertexCounts, faceVertexIndices, points = get_vtp_mesh_arrays(mesh_path)
                                
                                # Convert to trimesh format
                                faces = []
                                idx = 0
                                for count in faceVertexCounts:
                                    if count == 3:  # Only triangular faces
                                        face = [faceVertexIndices[idx], faceVertexIndices[idx+1], faceVertexIndices[idx+2]]
                                        faces.append(face)
                                    idx += count
                                
                                if len(faces) > 0:
                                    mesh = trimesh.Trimesh(vertices=points, faces=faces)
                                    base_geometry[body_name] = mesh
                                    print(f"Loaded geometry for {body_name}: {len(points)} vertices, {len(faces)} faces")
                                
                            except Exception as e:
                                print(f"Warning: Could not load mesh for {body_name}: {e}")
                        else:
                            print(f"Warning: Mesh file not found: {mesh_path}")
                            
    except Exception as e:
        print(f"Error parsing OpenSim model: {e}")
        traceback.print_exc()
    
    return base_geometry

def create_imu_box():
    """Create a box mesh for IMU visualization."""
    box = trimesh.creation.box(extents=imu_extents)
    return box

def load_calibration(calib_path):
    """Load camera calibration from .npz file."""
    if not os.path.exists(calib_path):
        print(f"Warning: Calibration file not found: {calib_path}")
        # Return default calibration
        return np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=np.float64)
    
    try:
        calib = np.load(calib_path)
        return calib['K']
    except Exception as e:
        print(f"Error loading calibration: {e}")
        # Return default calibration
        return np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=np.float64)

def create_camera(K):
    """Create camera from intrinsics."""
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    
    # Calculate field of view
    yfov = 2 * np.arctan(cy / fy)
    aspect_ratio = cx * 2 / (cy * 2)
    
    return pyrender.PerspectiveCamera(yfov=yfov, aspectRatio=aspect_ratio)

def render_mesh_frame(base_geometry, body_names, body_poses, camera, cam_pose, resolution=(640, 480)):
    """Render a single frame with body meshes and IMU boxes."""
    try:
        # Create scene
        scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0])
        
        # Add body meshes
        for body_idx, body_name in enumerate(body_names):
            if body_idx < len(body_poses):
                position, quat = body_poses[body_idx]
                transform = pose_to_matrix(position, quat)
                
                # Add body mesh if available
                if body_name in base_geometry:
                    mesh = base_geometry[body_name].copy()
                    mesh.apply_transform(transform)
                    
                    # Center and scale the mesh
                    min_bounds = mesh.bounds[0]
                    max_bounds = mesh.bounds[1]
                    center_x = (min_bounds[0] + max_bounds[0]) / 2.0
                    center_z = (min_bounds[2] + max_bounds[2]) / 2.0
                    translation = np.array([-center_x, 0, -center_z])
                    mesh.apply_translation(translation)
                    mesh.apply_scale(0.9)
                    
                    pyr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=True)
                    scene.add(pyr_mesh)
                
                # Add IMU box if this body has one
                if body_name in imu_offsets:
                    imu_box = create_imu_box()
                    
                    # Color based on body side
                    if 'r' in body_name:
                        color = [255, 0, 0, 255]  # Red for right
                    elif 'l' in body_name:
                        color = [0, 0, 255, 255]  # Blue for left
                    else:
                        color = [0, 255, 0, 255]  # Green for center (pelvis)
                    
                    imu_box.visual.face_colors = color
                    
                    # Apply IMU offset
                    imu_transform = transform.copy()
                    imu_offset = imu_offsets[body_name]
                    imu_transform[:3, 3] += transform[:3, :3] @ imu_offset
                    
                    imu_box.apply_transform(imu_transform)
                    pyr_imu = pyrender.Mesh.from_trimesh(imu_box)
                    scene.add(pyr_imu)
        
        # Add camera
        scene.add(camera, pose=cam_pose)
        
        # Add lighting
        main_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
        scene.add(main_light, pose=cam_pose)
        
        top_light_pose = np.eye(4)
        top_light_pose[:3, 3] = [0, 5.0, 0]
        top_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=1.0)
        scene.add(top_light, pose=top_light_pose)
        
        # Render
        renderer = pyrender.OffscreenRenderer(viewport_width=resolution[0], viewport_height=resolution[1])
        color, depth = renderer.render(scene)
        renderer.delete()
        
        return color
        
    except Exception as e:
        print(f"Error in render_mesh_frame: {e}")
        traceback.print_exc()
        raise

def generate_video_from_motion_complete(model_path, mot_path, calib_path, output_dir, progress_callback=None):
    """Complete video generation from OpenSim model and motion data."""
    
    print(f"Starting complete video generation...")
    print(f"Model: {model_path}")
    print(f"Motion: {mot_path}")
    print(f"Output: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up options for mot2quats
    optionsDict = {
        "outputFolder": output_dir,
        "columnsInDegrees": [
            "pelvis_tilt", "pelvis_list", "pelvis_rotation",
            "hip_flexion_r", "hip_adduction_r", "hip_rotation_r",
            "knee_angle_r", "knee_angle_r_beta", "ankle_angle_r",
            "subtalar_angle_r", "mtp_angle_r",
            "hip_flexion_l", "hip_adduction_l", "hip_rotation_l",
            "knee_angle_l", "knee_angle_l_beta", "ankle_angle_l",
            "subtalar_angle_l", "mtp_angle_l",
            "lumbar_extension", "lumbar_bending", "lumbar_rotation"
        ],
        "motionFormat": "localRotationsOnly",
        "activationSTO": False
    }
    
    # Get geometry path
    model_dir = os.path.dirname(model_path)
    geom_path = os.path.join(model_dir, "Geometry")
    
    if not os.path.exists(geom_path):
        # Try alternative geometry paths
        alt_paths = [
            os.path.join(os.path.dirname(model_dir), "Geometry"),
            os.path.join(output_dir, "..", "models", "Geometry"),
            os.path.join(output_dir, "..", "models", "imu_geometry")
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                geom_path = alt_path
                break
        else:
            print(f"Warning: No geometry directory found. Will only show IMU boxes.")
            geom_path = None
    
    # Cache base geometry
    base_geometry = {}
    if geom_path:
        base_geometry = cache_base_geometry(model_path, geom_path)
        print("Cached base geometry for bodies:", list(base_geometry.keys()))
    
    # Set up camera
    K = load_calibration(calib_path)
    camera = create_camera(K)
    cam_pose = np.eye(4)
    cam_pose[:3, 3] = [0, 0.75, 2]  # Position camera
    resolution = (640, 480)
    
    print("Camera intrinsics:\n", K)
    print("Camera pose:\n", cam_pose)
    
    # Convert motion to pose trajectories
    print("Converting motion data to pose trajectories...")
    try:
        motion_name, (body_names, times, pose_trajectories) = mot2quats(
            mot_path, None, {}, model_path, set(), optionsDict
        )
    except Exception as e:
        print(f"Error in mot2quats: {e}")
        traceback.print_exc()
        raise
    
    nFrames = len(times)
    print(f"Loaded {nFrames} frames for {len(body_names)} bodies")
    
    # Set up video writer
    video_path = os.path.join(output_dir, f"{motion_name}_video.mp4")
    video_writer = imageio.get_writer(video_path, fps=30)
    
    print(f"Generating video with {nFrames} frames...")
    
    # Process each frame
    successful_frames = 0
    for i in tqdm(range(nFrames), desc="Rendering frames"):
        try:
            # Get poses for this frame
            frame_poses = pose_trajectories[i]
            
            # Render frame
            color = render_mesh_frame(
                base_geometry, body_names, frame_poses, 
                camera, cam_pose, resolution
            )
            
            # Convert to uint8 and add time text
            frame = (color * 255).astype(np.uint8)
            
            # Add time text
            time_text = f"Time: {times[i]:.2f}s"
            cv2.putText(frame, time_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # Write frame
            video_writer.append_data(frame)
            successful_frames += 1
            
            # Progress callback
            if progress_callback:
                progress = (i + 1) / nFrames
                progress_callback(progress)
            
        except Exception as e:
            print(f"Error rendering frame {i}: {e}")
            # Write black frame as fallback
            black_frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
            cv2.putText(black_frame, "Error", (resolution[0]//2-50, resolution[1]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
            video_writer.append_data(black_frame)
    
    # Cleanup
    video_writer.close()
    gc.collect()
    
    print(f"Video saved to: {video_path} with {successful_frames}/{nFrames} frames")
    return video_path

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate video from OpenSim model and motion")
    parser.add_argument("-i", "--input", required=True, help="OpenSim model file (.osim)")
    parser.add_argument("-m", "--motion", required=True, help="Motion file (.mot)")
    parser.add_argument("-c", "--calib", help="Camera calibration file (.npz)")
    parser.add_argument("-o", "--output", default="./output", help="Output directory")
    
    args = parser.parse_args()
    
    # Generate video
    try:
        video_path = generate_video_from_motion_complete(
            args.input, 
            args.motion, 
            args.calib or "", 
            args.output
        )
        print(f"SUCCESS: Video generated at {video_path}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
"""
Complete video generation utility adapted from mbl_osim2obj/osim2video.py
Generates MP4 videos from OpenSim models and motion data with IMU visualization.
"""

import os, sys, math, time, gc
import numpy as np
import cv2
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import xml.etree.ElementTree as ET
import opensim as osim
import quaternion
import trimesh
import pyrender
import imageio
from tqdm import tqdm
import traceback
from pathlib import Path

# Import the mot2quats utility
from .mot2quats import mot2quats

# Global parameters for IMU boxes
imu_extents = (0.05, 0.1, 0.05)  # (width, height, depth)

# IMU placement offsets for each body segment
imu_offsets = {
    "pelvis": np.array([-0.15, 0.00, 0.00]),
    "femur_r": np.array([0.0, -0.20, 0.05]),
    "tibia_r": np.array([0.0, -0.15, 0.05]),
    "calcn_r": np.array([0.12, 0.03, 0.0]),
    "femur_l": np.array([0.0, -0.20, -0.05]),
    "tibia_l": np.array([0.0, -0.15, -0.05]),
    "calcn_l": np.array([0.12, 0.03, 0.0]),
}

def pose_to_matrix(position, quat):
    """Convert pose (position and quaternion) to 4x4 transform matrix."""
    try:
        R = quaternion.as_rotation_matrix(quat)
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = position
        return T
    except Exception as e:
        print(f"Error in pose_to_matrix: {e}")
        traceback.print_exc()
        raise

def get_vtp_mesh_arrays(meshPath):
    """Load VTP mesh file and return face counts, indices, and vertices."""
    if not os.path.exists(meshPath):
        raise FileNotFoundError(f"Mesh file not found: {meshPath}")
    try:
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(meshPath)
        reader.Update()
        polyData = reader.GetOutput()
        faces_vtk = polyData.GetPolys()
        cellCount = faces_vtk.GetNumberOfCells()
        faceArray = vtk_to_numpy(faces_vtk.GetData())
        i = 0
        faceVertexCounts = []
        faceVertexIndices = []
        for _ in range(cellCount):
            count = int(faceArray[i])
            faceVertexCounts.append(count)
            for j in range(count):
                faceVertexIndices.append(int(faceArray[i+1+j]))
            i += count + 1
        points_vtk = polyData.GetPoints().GetData()
        points = vtk_to_numpy(points_vtk)
        return faceVertexCounts, faceVertexIndices, points
    except Exception as e:
        print(f"Error processing mesh {meshPath}: {e}")
        traceback.print_exc()
        raise

def cache_base_geometry(osimPath, geomPath):
    """Cache base geometry from OpenSim model."""
    base_geometry = {}
    
    try:
        # Parse the OpenSim model to find mesh files
        tree = ET.parse(osimPath)
        root = tree.getroot()
        
        # Find all Body elements with attached geometry
        for body in root.findall(".//Body"):
            body_name = body.get("name")
            
            # Find attached geometry (Mesh elements)
            for attached_geom in body.findall(".//AttachedGeometry"):
                for mesh in attached_geom.findall(".//Mesh"):
                    mesh_file = mesh.get("mesh_file")
                    if mesh_file:
                        mesh_path = os.path.join(geomPath, mesh_file)
                        if os.path.exists(mesh_path):
                            try:
                                faceVertexCounts, faceVertexIndices, points = get_vtp_mesh_arrays(mesh_path)
                                
                                # Convert to trimesh format
                                faces = []
                                idx = 0
                                for count in faceVertexCounts:
                                    if count == 3:  # Only triangular faces
                                        face = [faceVertexIndices[idx], faceVertexIndices[idx+1], faceVertexIndices[idx+2]]
                                        faces.append(face)
                                    idx += count
                                
                                if len(faces) > 0:
                                    mesh = trimesh.Trimesh(vertices=points, faces=faces)
                                    base_geometry[body_name] = mesh
                                    print(f"Loaded geometry for {body_name}: {len(points)} vertices, {len(faces)} faces")
                                
                            except Exception as e:
                                print(f"Warning: Could not load mesh for {body_name}: {e}")
                        else:
                            print(f"Warning: Mesh file not found: {mesh_path}")
                            
    except Exception as e:
        print(f"Error parsing OpenSim model: {e}")
        traceback.print_exc()
    
    return base_geometry

def create_imu_box():
    """Create a box mesh for IMU visualization."""
    box = trimesh.creation.box(extents=imu_extents)
    return box

def load_calibration(calib_path):
    """Load camera calibration from .npz file."""
    if not os.path.exists(calib_path):
        print(f"Warning: Calibration file not found: {calib_path}")
        # Return default calibration
        return np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=np.float64)
    
    try:
        calib = np.load(calib_path)
        return calib['K']
    except Exception as e:
        print(f"Error loading calibration: {e}")
        # Return default calibration
        return np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=np.float64)

def create_camera(K):
    """Create camera from intrinsics."""
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    
    # Calculate field of view
    yfov = 2 * np.arctan(cy / fy)
    aspect_ratio = cx * 2 / (cy * 2)
    
    return pyrender.PerspectiveCamera(yfov=yfov, aspectRatio=aspect_ratio)

def render_mesh_frame(base_geometry, body_names, body_poses, camera, cam_pose, resolution=(640, 480)):
    """Render a single frame with body meshes and IMU boxes."""
    try:
        # Create scene
        scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0])
        
        # Add body meshes
        for body_idx, body_name in enumerate(body_names):
            if body_idx < len(body_poses):
                position, quat = body_poses[body_idx]
                transform = pose_to_matrix(position, quat)
                
                # Add body mesh if available
                if body_name in base_geometry:
                    mesh = base_geometry[body_name].copy()
                    mesh.apply_transform(transform)
                    
                    # Center and scale the mesh
                    min_bounds = mesh.bounds[0]
                    max_bounds = mesh.bounds[1]
                    center_x = (min_bounds[0] + max_bounds[0]) / 2.0
                    center_z = (min_bounds[2] + max_bounds[2]) / 2.0
                    translation = np.array([-center_x, 0, -center_z])
                    mesh.apply_translation(translation)
                    mesh.apply_scale(0.9)
                    
                    pyr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=True)
                    scene.add(pyr_mesh)
                
                # Add IMU box if this body has one
                if body_name in imu_offsets:
                    imu_box = create_imu_box()
                    
                    # Color based on body side
                    if 'r' in body_name:
                        color = [255, 0, 0, 255]  # Red for right
                    elif 'l' in body_name:
                        color = [0, 0, 255, 255]  # Blue for left
                    else:
                        color = [0, 255, 0, 255]  # Green for center (pelvis)
                    
                    imu_box.visual.face_colors = color
                    
                    # Apply IMU offset
                    imu_transform = transform.copy()
                    imu_offset = imu_offsets[body_name]
                    imu_transform[:3, 3] += transform[:3, :3] @ imu_offset
                    
                    imu_box.apply_transform(imu_transform)
                    pyr_imu = pyrender.Mesh.from_trimesh(imu_box)
                    scene.add(pyr_imu)
        
        # Add camera
        scene.add(camera, pose=cam_pose)
        
        # Add lighting
        main_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
        scene.add(main_light, pose=cam_pose)
        
        top_light_pose = np.eye(4)
        top_light_pose[:3, 3] = [0, 5.0, 0]
        top_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=1.0)
        scene.add(top_light, pose=top_light_pose)
        
        # Render
        renderer = pyrender.OffscreenRenderer(viewport_width=resolution[0], viewport_height=resolution[1])
        color, depth = renderer.render(scene)
        renderer.delete()
        
        return color
        
    except Exception as e:
        print(f"Error in render_mesh_frame: {e}")
        traceback.print_exc()
        raise

def generate_video_from_motion_complete(model_path, mot_path, calib_path, output_dir, progress_callback=None):
    """Complete video generation from OpenSim model and motion data."""
    
    print(f"Starting complete video generation...")
    print(f"Model: {model_path}")
    print(f"Motion: {mot_path}")
    print(f"Output: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up options for mot2quats
    optionsDict = {
        "outputFolder": output_dir,
        "columnsInDegrees": [
            "pelvis_tilt", "pelvis_list", "pelvis_rotation",
            "hip_flexion_r", "hip_adduction_r", "hip_rotation_r",
            "knee_angle_r", "knee_angle_r_beta", "ankle_angle_r",
            "subtalar_angle_r", "mtp_angle_r",
            "hip_flexion_l", "hip_adduction_l", "hip_rotation_l",
            "knee_angle_l", "knee_angle_l_beta", "ankle_angle_l",
            "subtalar_angle_l", "mtp_angle_l",
            "lumbar_extension", "lumbar_bending", "lumbar_rotation"
        ],
        "motionFormat": "localRotationsOnly",
        "activationSTO": False
    }
    
    # Get geometry path
    model_dir = os.path.dirname(model_path)
    geom_path = os.path.join(model_dir, "Geometry")
    
    if not os.path.exists(geom_path):
        # Try alternative geometry paths
        alt_paths = [
            os.path.join(os.path.dirname(model_dir), "Geometry"),
            os.path.join(output_dir, "..", "models", "Geometry"),
            os.path.join(output_dir, "..", "models", "imu_geometry")
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                geom_path = alt_path
                break
        else:
            print(f"Warning: No geometry directory found. Will only show IMU boxes.")
            geom_path = None
    
    # Cache base geometry
    base_geometry = {}
    if geom_path:
        base_geometry = cache_base_geometry(model_path, geom_path)
        print("Cached base geometry for bodies:", list(base_geometry.keys()))
    
    # Set up camera
    K = load_calibration(calib_path)
    camera = create_camera(K)
    cam_pose = np.eye(4)
    cam_pose[:3, 3] = [0, 0.75, 2]  # Position camera
    resolution = (640, 480)
    
    print("Camera intrinsics:\n", K)
    print("Camera pose:\n", cam_pose)
    
    # Convert motion to pose trajectories
    print("Converting motion data to pose trajectories...")
    try:
        motion_name, (body_names, times, pose_trajectories) = mot2quats(
            mot_path, None, {}, model_path, set(), optionsDict
        )
    except Exception as e:
        print(f"Error in mot2quats: {e}")
        traceback.print_exc()
        raise
    
    nFrames = len(times)
    print(f"Loaded {nFrames} frames for {len(body_names)} bodies")
    
    # Set up video writer
    video_path = os.path.join(output_dir, f"{motion_name}_video.mp4")
    video_writer = imageio.get_writer(video_path, fps=30)
    
    print(f"Generating video with {nFrames} frames...")
    
    # Process each frame
    successful_frames = 0
    for i in tqdm(range(nFrames), desc="Rendering frames"):
        try:
            # Get poses for this frame
            frame_poses = pose_trajectories[i]
            
            # Render frame
            color = render_mesh_frame(
                base_geometry, body_names, frame_poses, 
                camera, cam_pose, resolution
            )
            
            # Convert to uint8 and add time text
            frame = (color * 255).astype(np.uint8)
            
            # Add time text
            time_text = f"Time: {times[i]:.2f}s"
            cv2.putText(frame, time_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # Write frame
            video_writer.append_data(frame)
            successful_frames += 1
            
            # Progress callback
            if progress_callback:
                progress = (i + 1) / nFrames
                progress_callback(progress)
            
        except Exception as e:
            print(f"Error rendering frame {i}: {e}")
            # Write black frame as fallback
            black_frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
            cv2.putText(black_frame, "Error", (resolution[0]//2-50, resolution[1]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
            video_writer.append_data(black_frame)
    
    # Cleanup
    video_writer.close()
    gc.collect()
    
    print(f"Video saved to: {video_path} with {successful_frames}/{nFrames} frames")
    return video_path

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate video from OpenSim model and motion")
    parser.add_argument("-i", "--input", required=True, help="OpenSim model file (.osim)")
    parser.add_argument("-m", "--motion", required=True, help="Motion file (.mot)")
    parser.add_argument("-c", "--calib", help="Camera calibration file (.npz)")
    parser.add_argument("-o", "--output", default="./output", help="Output directory")
    
    args = parser.parse_args()
    
    # Generate video
    try:
        video_path = generate_video_from_motion_complete(
            args.input, 
            args.motion, 
            args.calib or "", 
            args.output
        )
        print(f"SUCCESS: Video generated at {video_path}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
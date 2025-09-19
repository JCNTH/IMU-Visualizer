#!/usr/bin/env python3
"""
osim_video_generator.py

Simplified video generation utility for mbl_imuviz project.
Converts OpenSim model and motion data to MP4 video.
"""

import os, sys, math, time, gc
import numpy as np
import cv2
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import xml.etree.ElementTree as ET
import opensim as osim
import quaternion  # requires numpy-quaternion
import trimesh
import pyrender
import imageio
from tqdm import tqdm
import traceback
from pathlib import Path

# Import the mot2quats utility
from .mot2quats import mot2quats

# Global parameters for IMU boxes
imu_extents = (0.05, 0.1, 0.05)  # (width, height, depth) - rotated 90° to be taller

# Define fixed IMU placement offsets for each body segment
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
    R = quaternion.as_rotation_matrix(quat)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = position
    return T

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

def create_imu_box_mesh(extents, color=[1.0, 0.0, 0.0]):
    """Create a box mesh for IMU visualization."""
    box = trimesh.creation.box(extents=extents)
    box.visual.face_colors = [int(c * 255) for c in color] + [255]
    return box

def create_default_camera_calibration():
    """Create a default camera calibration if none provided."""
    K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=np.float64)
    R = np.eye(3, dtype=np.float64)
    T = np.array([0, 0, -3], dtype=np.float64)
    return K, R, T

def load_camera_calibration(calib_path):
    """Load camera calibration from .npz file."""
    if not os.path.exists(calib_path):
        print(f"Warning: Calibration file not found: {calib_path}")
        print("Using default camera calibration")
        return create_default_camera_calibration()
    
    try:
        calib = np.load(calib_path)
        K = calib['K']
        R = calib['R'] 
        T = calib['T']
        return K, R, T
    except Exception as e:
        print(f"Error loading calibration: {e}")
        print("Using default camera calibration")
        return create_default_camera_calibration()

def generate_video_from_motion(model_path, mot_path, calib_path, output_dir, progress_callback=None):
    """Generate video from OpenSim model and motion data."""
    
    print(f"Starting video generation...")
    print(f"Model: {model_path}")
    print(f"Motion: {mot_path}")
    print(f"Output: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load camera calibration
    K, R, T = load_camera_calibration(calib_path)
    
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
        "motionFormat": "localRotationsOnly"
    }
    
    # Convert motion to pose trajectories
    print("Converting motion data to pose trajectories...")
    try:
        motion_name, (body_names, times, pose_trajectories) = mot2quats(
            mot_path, model_path, set(), optionsDict
        )
    except Exception as e:
        print(f"Error in mot2quats: {e}")
        traceback.print_exc()
        raise
    
    print(f"Loaded {len(times)} frames for {len(body_names)} bodies")
    
    # Load OpenSim model to get mesh information
    try:
        model = osim.Model(model_path)
        state = model.initSystem()
    except Exception as e:
        print(f"Error loading OpenSim model: {e}")
        raise
    
    # Get model directory for geometry files
    model_dir = os.path.dirname(model_path)
    geometry_dir = os.path.join(model_dir, "Geometry")
    
    if not os.path.exists(geometry_dir):
        # Try alternative geometry directory
        geometry_dir = os.path.join(os.path.dirname(model_dir), "Geometry")
    
    # Load body meshes
    body_meshes = {}
    print("Loading body meshes...")
    
    # Parse OSIM file to get mesh information
    try:
        tree = ET.parse(model_path)
        root = tree.getroot()
        
        # Find all mesh elements
        for body_elem in root.findall(".//Body"):
            body_name = body_elem.get("name")
            
            # Find attached geometry
            for mesh_elem in body_elem.findall(".//Mesh"):
                mesh_file = mesh_elem.get("file")
                if mesh_file:
                    mesh_path = os.path.join(geometry_dir, mesh_file)
                    if os.path.exists(mesh_path):
                        try:
                            vertices, faces = get_vtp_mesh_arrays(mesh_path)
                            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
                            body_meshes[body_name] = mesh
                            print(f"Loaded mesh for {body_name}: {len(vertices)} vertices, {len(faces)} faces")
                        except Exception as e:
                            print(f"Warning: Could not load mesh for {body_name}: {e}")
                    else:
                        print(f"Warning: Mesh file not found: {mesh_path}")
    
    except Exception as e:
        print(f"Error parsing model file: {e}")
        # Continue without meshes - will only show IMU boxes
    
    # Create IMU box meshes
    imu_meshes = {}
    for body_name in imu_offsets.keys():
        if body_name in body_names:
            color = [1.0, 0.0, 0.0] if 'r' in body_name else [0.0, 0.0, 1.0]
            if 'pelvis' in body_name:
                color = [0.0, 1.0, 0.0]
            imu_meshes[body_name] = create_imu_box_mesh(imu_extents, color)
    
    # Set up video parameters
    width, height = 640, 480
    fps = 30
    
    # Calculate frame indices to sample
    total_frames = len(times)
    target_duration = 10  # seconds
    target_frames = min(fps * target_duration, total_frames)
    frame_indices = np.linspace(0, total_frames - 1, target_frames, dtype=int)
    
    # Set up video writer
    video_path = os.path.join(output_dir, f"{motion_name}_video.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    
    print(f"Generating video with {len(frame_indices)} frames...")
    
    # Process each frame
    for i, frame_idx in enumerate(tqdm(frame_indices, desc="Rendering frames")):
        try:
            # Create scene
            scene = pyrender.Scene()
            
            # Get poses for this frame
            frame_poses = pose_trajectories[frame_idx]
            
            # Add body meshes to scene
            for body_idx, body_name in enumerate(body_names):
                if body_idx < len(frame_poses):
                    position, quat = frame_poses[body_idx]
                    transform = pose_to_matrix(position, quat)
                    
                    # Add body mesh if available
                    if body_name in body_meshes:
                        mesh_node = scene.add(
                            pyrender.Mesh.from_trimesh(body_meshes[body_name]),
                            pose=transform
                        )
                    
                    # Add IMU box if this body has one
                    if body_name in imu_meshes:
                        # Apply IMU offset
                        imu_transform = transform.copy()
                        imu_offset = imu_offsets[body_name]
                        imu_transform[:3, 3] += transform[:3, :3] @ imu_offset
                        
                        imu_node = scene.add(
                            pyrender.Mesh.from_trimesh(imu_meshes[body_name]),
                            pose=imu_transform
                        )
            
            # Set up camera
            camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0, aspectRatio=width/height)
            camera_pose = np.eye(4)
            camera_pose[:3, :3] = R.T  # Camera to world rotation
            camera_pose[:3, 3] = -R.T @ T  # Camera position in world coordinates
            scene.add(camera, pose=camera_pose)
            
            # Add lighting
            light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
            scene.add(light, pose=camera_pose)
            
            # Render
            renderer = pyrender.OffscreenRenderer(width, height)
            color, depth = renderer.render(scene)
            renderer.delete()
            
            # Convert to BGR for OpenCV
            frame = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)
            
            # Add time text
            time_text = f"Time: {times[frame_idx]:.2f}s"
            cv2.putText(frame, time_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Write frame
            video_writer.write(frame)
            
            # Progress callback
            if progress_callback:
                progress = (i + 1) / len(frame_indices)
                progress_callback(progress)
            
        except Exception as e:
            print(f"Error rendering frame {i}: {e}")
            # Write black frame as fallback
            black_frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.putText(black_frame, "Error", (width//2-50, height//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
            video_writer.write(black_frame)
    
    # Cleanup
    video_writer.release()
    gc.collect()
    
    print(f"Video saved to: {video_path}")
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
        video_path = generate_video_from_motion(
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
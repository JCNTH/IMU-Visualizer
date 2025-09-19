#!/usr/bin/env python3
"""
osim2video_imu.py - Adapted from osim2IMUvideo.py

This script:
  1. Reads an OpenSim model (.osim) and a motion file (.mot), uses a mot2quats routine to compute per‐frame body poses,
     and renders each frame using the attached mesh geometry plus small IMU boxes on each body segment.
  2. The final frames are assembled into a video with a white background.
  3. Additionally, for each frame an OBJ file (combining skeleton and IMU geometry) is saved to an output folder.

A calibration file (calib.npz) must contain:
    - K: camera intrinsics (3x3 matrix)
    - R: camera-to-world rotation (3x3 matrix)
    - T: camera-to-world translation (3-element vector)
"""

import os, sys, math, io
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
from pathlib import Path

# Global parameters for IMU boxes.
imu_extents = (0.05, 0.1, 0.05)  # (width, height, depth) - rotated 90° to be taller

# Define fixed IMU placement offsets (in the body's local coordinate system) for each body segment.
imu_offsets = {
    "pelvis": np.array([-0.15, 0.00, 0.00]),    # Adjusted placement on pelvis
    "femur_r": np.array([0.0, -0.20, 0.05]),    # Placed on lateral side of right thigh
    "tibia_r": np.array([0.0, -0.15, 0.05]),    # Placed on lateral side of right shank
    "calcn_r": np.array([0.12, 0.03, 0.0]),     # Placed on top of right foot
    "femur_l": np.array([0.0, -0.20, -0.05]),   # Placed on lateral side of left thigh
    "tibia_l": np.array([0.0, -0.15, -0.05]),   # Placed on lateral side of left shank
    "calcn_l": np.array([0.12, 0.03, 0.0]),     # Placed on top of left foot
}

# Simple debug print function
def debug_print(message, level="INFO"):
    """Print debug messages with level indicator"""
    prefix = f"[{level}]"
    print(f"{prefix} {message}")

##############################
# Helper: Convert pose (position + quaternion) to 4x4 transform matrix.
##############################
def pose_to_matrix(position, quat):
    R = quaternion.as_rotation_matrix(quat)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = position
    return T

##############################
# VTK Mesh Loader (for .vtp files)
##############################
def get_vtp_mesh_arrays(meshPath):
    if not os.path.exists(meshPath):
        raise FileNotFoundError(f"Mesh file not found: {meshPath}")
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

def write_obj_file(filename, vertices, faces):
    with open(filename, "w") as f:
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for face in faces:
            face_str = " ".join(str(idx+1) for idx in face)
            f.write(f"f {face_str}\n")

##############################
# Build a trimesh from in‐memory vertices and faces.
##############################
def mesh_from_memory(vertices, faces):
    """Create a trimesh from vertices and faces lists"""
    if not vertices or not faces:
        print(f"ERROR: mesh_from_memory - empty data: vertices={len(vertices)}, faces={len(faces)}")
        return None
        
    print(f"DEBUG: Creating mesh from {len(vertices)} vertices, {len(faces)} faces")
    
    lines = []
    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    for face in faces:
        if len(face) >= 3:  # Ensure valid face
            lines.append("f " + " ".join(str(i+1) for i in face))
        else:
            print(f"WARNING: Skipping invalid face with {len(face)} vertices: {face}")
    
    obj_data = "\n".join(lines)
    obj_file = io.StringIO(obj_data)
    
    try:
        mesh = trimesh.load(obj_file, file_type='obj')
        if mesh.is_empty:
            print("ERROR: Created mesh is empty")
            return None
        print(f"DEBUG: Successfully created mesh with {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        print(f"DEBUG: Mesh bounds: {mesh.bounds}")
        return mesh
    except Exception as e:
        print(f"ERROR: Failed to create mesh: {e}")
        return None

##############################
# Create a small IMU box in local coords.
##############################
def create_imu_box(extents=imu_extents):
    box = trimesh.creation.box(extents=extents)
    return box.vertices, box.faces

##############################
# Create an IMU box with optional local rotation.
##############################
def create_imu_box_with_rotation(T_body, offsetLocal, extents,
                                 rotateDeg=0.0, rotateAxis=np.array([0, 0, 1])):
    """
    Creates a small IMU box and transforms it into world coordinates:
      1) An optional local rotation of rotateDeg (degrees) about rotateAxis
      2) A local translation offsetLocal
      3) Then apply the body transform T_body
    """
    # 1) Create base IMU box in local coords
    boxVerts, boxFaces = create_imu_box(extents=extents)

    # 2) Build the local transform
    T_local = np.eye(4)
    if rotateDeg != 0.0:
        theta = math.radians(rotateDeg)
        axis = rotateAxis / np.linalg.norm(rotateAxis)
        ux, uy, uz = axis
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        R_mat = np.array([
            [cos_t + ux*ux*(1-cos_t),   ux*uy*(1-cos_t) - uz*sin_t, ux*uz*(1-cos_t) + uy*sin_t, 0],
            [uy*ux*(1-cos_t) + uz*sin_t, cos_t + uy*uy*(1-cos_t),   uy*uz*(1-cos_t) - ux*sin_t, 0],
            [uz*ux*(1-cos_t) - uy*sin_t, uz*uy*(1-cos_t) + ux*sin_t, cos_t + uz*uz*(1-cos_t),   0],
            [0, 0, 0, 1]
        ])
        T_local = T_local @ R_mat

    # Then translation
    T_local[0, 3] = offsetLocal[0]
    T_local[1, 3] = offsetLocal[1]
    T_local[2, 3] = offsetLocal[2]

    # 3) Combine local transform with body transform
    T_full = T_body @ T_local

    # 4) Transform vertices to world
    N = boxVerts.shape[0]
    boxVerts_h = np.hstack([boxVerts, np.ones((N, 1))])  # shape: (N,4)
    boxVerts_w = (T_full @ boxVerts_h.T).T[:, :3]        # shape: (N,3)

    return boxVerts_w, boxFaces

##############################
# Render a combined frame (skeleton + IMU) with white background.
##############################
def render_combined_frame(combined_vertices, combined_faces, camera, cam_pose, resolution):
    try:
        # Validate input data
        if not combined_vertices or not combined_faces:
            print(f"WARNING: Empty geometry data - vertices: {len(combined_vertices)}, faces: {len(combined_faces)}")
            return np.ones((resolution[1], resolution[0], 4), dtype=np.uint8) * 128  # Gray image
        
        print(f"DEBUG: Rendering frame with {len(combined_vertices)} vertices, {len(combined_faces)} faces")
        
        # Create a trimesh from the combined geometry
        mesh = mesh_from_memory(combined_vertices, combined_faces)
        
        if not isinstance(mesh, trimesh.Trimesh):
            print(f"ERROR: Failed to create valid trimesh object: {type(mesh)}")
            return np.ones((resolution[1], resolution[0], 4), dtype=np.uint8) * 128
        
        print(f"DEBUG: Original mesh bounds: {mesh.bounds}")
        
        # Center the mesh properly (like obj2video.py)
        # Move the minimum y (feet) to y=0, and center horizontally in X and Z
        min_bounds = mesh.bounds[0]  # [min_x, min_y, min_z]
        max_bounds = mesh.bounds[1]  # [max_x, max_y, max_z]
        center_x = (min_bounds[0] + max_bounds[0]) / 2.0
        center_z = (min_bounds[2] + max_bounds[2]) / 2.0
        translation = np.array([-center_x, -min_bounds[1], -center_z])  # Place feet on ground
        mesh.apply_translation(translation)
        print(f"DEBUG: Applied translation: {translation}")
        print(f"DEBUG: New mesh bounds: {mesh.bounds}")
        
        # Convert to pyrender mesh
        pyr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=True)
        
        # Create scene with light gray background (like obj2video.py for better visibility)
        scene = pyrender.Scene(bg_color=[0.8, 0.8, 0.8, 1.0])
        scene.add(pyr_mesh)
        scene.add(camera, pose=cam_pose)
        
        # Add a directional light (matching obj2video.py intensity)
        light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
        scene.add(light, pose=cam_pose)
        
        # Render the scene
        renderer = pyrender.OffscreenRenderer(viewport_width=resolution[0], viewport_height=resolution[1])
        color, depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        renderer.delete()
        
        print(f"DEBUG: Rendered frame shape: {color.shape}, non-zero pixels: {np.count_nonzero(color)}")
        return color
    except Exception as e:
        print(f"Rendering error: {e}")
        import traceback
        traceback.print_exc()
        return np.ones((resolution[1], resolution[0], 4), dtype=np.uint8) * 128  # Gray image

##############################
# mot2quats routine.
##############################
def mot2quats(motionPath, modelPath, muscleNames, optionsDict):
    print(f"Processing motion: {motionPath}")
    motion = osim.Storage(motionPath)
    # Convert degrees to radians if needed
    if motion.isInDegrees():
        if optionsDict.get("columnsInDegrees", []):
            print("Converting degree data to radians.")
            for dof in optionsDict["columnsInDegrees"]:
                try:
                    dofIndex = motion.getStateIndex(dof)
                    motion.multiplyColumn(dofIndex, math.pi / 180.0)
                except:
                    # try alt name
                    alt_dof = dof.replace("angle", "flexion")
                    try:
                        dofIndex = motion.getStateIndex(alt_dof)
                        print(f"Using alternate column name: {alt_dof} for conversion.")
                        motion.multiplyColumn(dofIndex, math.pi / 180.0)
                    except:
                        print(f"Column not found: {dof} or {alt_dof}; skipping.")
                        continue
            motion.setInDegrees(False)
        else:
            print("Motion data is in degrees; please supply columnsInDegrees.")
            return None
    motionName = os.path.splitext(os.path.basename(motionPath))[0]
    print(f"Motion name: {motionName}")

    # Load the model & build the trajectory
    model = osim.Model(modelPath)
    model.initSystem()
    motionTrajectory = osim.StatesTrajectory.createFromStatesStorage(model, motion, True, True)
    print("Trajectory size:", motionTrajectory.getSize())

    # Build list of (body name, body, joint)
    jointList = model.getJointList()
    bodyList = model.getBodyList()
    workingBodyList = []
    bodyNames = []
    jIter = jointList.begin()
    bIter = bodyList.begin()
    while jIter != jointList.end():
        workingBodyList.append((bIter.getName(), bIter.deref(), jIter.deref()))
        bodyNames.append(bIter.getName())
        jIter.next()
        bIter.next()

    poseTrajectories = []
    times = []
    print("Computing pose trajectories...")
    for i in range(motionTrajectory.getSize()):
        state = motionTrajectory.get(i)
        model.realizePosition(state)
        times.append(state.getTime())
        framePoses = []
        for (nm, body, joint) in workingBodyList:
            pos_g = body.getPositionInGround(state)
            rot_g = body.getRotationInGround(state)
            pos = np.array([pos_g.get(j) for j in range(3)])
            quat_osim = rot_g.convertRotationToQuaternion()
            qval = np.quaternion(quat_osim.get(0), quat_osim.get(1),
                                 quat_osim.get(2), quat_osim.get(3))
            framePoses.append((pos, qval))
        poseTrajectories.append(framePoses)

    return motionName, (bodyNames, times, poseTrajectories)

##############################
# Camera functions.
##############################
def load_calibration(calib_path):
    calib = np.load(calib_path, allow_pickle=True)
    K = calib["K"]
    return K

def create_camera(K, znear=0.1, zfar=1000.0):
    fx = K[0, 0]
    fy = K[1, 1]
    cx = K[0, 2]
    cy = K[1, 2]
    return pyrender.IntrinsicsCamera(fx=fx, fy=fy, cx=cx, cy=cy, znear=znear, zfar=zfar)

##############################
# Main export function
##############################
def generate_imu_video(osim_path, motion_path, calib_path, output_video_path, 
                       geometry_path=None, output_dir=None, start_frame=None, end_frame=None, 
                       skip_frames=1, resolution=(960, 540), fps=30):
    """
    Generate IMU video from OpenSim files.
    
    Args:
        osim_path: Path to OpenSim model (.osim)
        motion_path: Path to motion file (.mot) 
        calib_path: Path to calibration file (.npz)
        output_video_path: Path for output video
        geometry_path: Path to geometry directory (optional)
        output_dir: Directory for temporary files (optional)
        start_frame: Start frame index (optional, 0-based)
        end_frame: End frame index (optional, exclusive)
        skip_frames: Skip every N frames for speed (default: 1, no skipping)
        resolution: Video resolution tuple (width, height) (default: 960x540)
        fps: Frames per second (default: 30)
    
    Returns:
        str: Path to generated video
    """
    try:
        # Set default paths (use the working Model structure)
        if geometry_path is None:
            geometry_path = "./Model/Geometry"
        
        if output_dir is None:
            output_dir = str(Path(output_video_path).parent / "frames")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Options for processing
        optionsDict = {
            "outputFolder": output_dir,
                         "columnsInDegrees": [
                 "pelvis_tilt", "pelvis_list", "pelvis_rot", "pelvis_rotation", "pelvis_tx", "pelvis_ty", "pelvis_tz", 
                 "hip_flexion_r", "hip_adduction_r", "hip_rotation_r",
                 "knee_adduction_r", "knee_rotation_r", "knee_flexion_r", "knee_angle_r", "knee_angle_r_beta", 
                 "ankle_adduction_r", "ankle_rotation_r", "ankle_flexion_r", "ankle_angle_r", "subtalar_angle_r", "mtp_angle_r",
                 "hip_flexion_l", "hip_adduction_l", "hip_rotation_l",
                 "knee_adduction_l", "knee_rotation_l", "knee_flexion_l", "knee_angle_l", "knee_angle_l_beta", 
                 "ankle_adduction_l", "ankle_rotation_l", "ankle_flexion_l", "ankle_angle_l", "subtalar_angle_l", "mtp_angle_l",
                 "lumbar_extension", "lumbar_bending", "lumbar_rotation"
             ],
            "motionFormat": "localRotationsOnly",
            "activationSTO": False
        }
        
        # Generate frames
        frames = export_obj_frames_withIMU(
            osim_path, geometry_path, motion_path,
            output_dir, optionsDict, calib_path,
            start_frame=start_frame, end_frame=end_frame, 
            skip_frames=skip_frames, resolution=resolution
        )
        
        if not frames:
            raise RuntimeError("No frames rendered")
        
        # Write video
        print(f"Writing final video to: {output_video_path} at {fps} fps")
        imageio.mimwrite(output_video_path, frames, fps=fps)
        print(f"Done. Final video saved to: {output_video_path}")
        
        return output_video_path
        
    except Exception as e:
        print(f"Error generating IMU video: {e}")
        raise

def export_obj_frames_withIMU(osimPath, geomPath, motionPath,
                              outputFolder, optionsDict, calib_path,
                              start_frame=None, end_frame=None, skip_frames=1, 
                              resolution=(960, 540)):
    # 1) --- CACHE BASE GEOMETRY ONCE ---
    print(f"Parsing OSIM file: {osimPath}")
    tree = ET.parse(osimPath)
    root = tree.getroot()
    bodySet = root.find("./Model/BodySet")
    base_body_geometry = {}
    for bodyElem in bodySet.findall("./objects/Body"):
        bname = bodyElem.get("name")
        meshes = []
        for meshElem in bodyElem.findall("./attached_geometry/Mesh"):
            meshFile = os.path.join(geomPath, meshElem.find("mesh_file").text.strip())
            scales = [float(x) for x in meshElem.findtext("scale_factors", "1 1 1").split()]
            fcCounts, fcIndices, pts_local = get_vtp_mesh_arrays(meshFile)
            meshes.append({
                "pts_local": pts_local,
                "scales": scales,
                "faceCounts": fcCounts,
                "faceIndices": fcIndices
            })
        if meshes:
            base_body_geometry[bname] = meshes

    try:
        from tqdm import tqdm
    except ImportError:
        # Fallback if tqdm is not available
        def tqdm(iterable, desc="Processing"):
            return iterable

    # 2) SET UP CAMERA
    print(f"Loading calibration: {calib_path}")
    K = np.load(calib_path)["K"]
    camera = create_camera(K)
    # Use camera position from working scripts (obj2video.py pattern)
    cam_pose = np.eye(4)
    cam_pose[:3, 3] = [0, 1, 2]  # Match working scripts
    print("Using camera intrinsics from calibration:")
    print("K:\n", K)
    print("Camera pose (camera-to-world):\n", cam_pose)

    # 3) LOAD MOTION TRAJECTORY
    result = mot2quats(motionPath, osimPath, {}, optionsDict)
    if result is None:
        raise RuntimeError("Failed to process motion data")
        
    _, (bodyNames, times, poseTrajectories) = result
    nFrames = len(times)
    
    # Apply frame range limits
    actual_start = start_frame if start_frame is not None else 0
    actual_end = min(end_frame if end_frame is not None else nFrames, nFrames)
    
    # Generate frame indices with skipping
    frame_indices = list(range(actual_start, actual_end, skip_frames))
    
    print(f"Total frames in motion: {nFrames}")
    print(f"Rendering frames: {actual_start} to {actual_end-1} (every {skip_frames} frames)")
    print(f"Frames to render: {len(frame_indices)}")

    # 4) EXPORT + RENDER WITH PROGRESS BAR
    frames = []
    for i, fIdx in enumerate(tqdm(frame_indices, desc="Rendering frames")):
        tVal = times[fIdx]
        framePoses = poseTrajectories[fIdx]

        combined_vertices = []
        combined_faces = []
        vertex_offset = 0

        # build skeleton + IMU geometry for this frame
        skeleton_vertices_count = 0
        imu_vertices_count = 0
        
        for bname, meshes in base_body_geometry.items():
            if bname not in bodyNames:
                continue
            iB = bodyNames.index(bname)
            pos, quat = framePoses[iB]
            T_world = pose_to_matrix(pos, quat)

            # **skeleton geometry**
            for seg in meshes:
                pts = seg["pts_local"]
                scales = seg["scales"]
                # scale -> transform -> accumulate
                N = pts.shape[0]
                S = np.diag(scales + [1])
                hom = np.hstack([pts, np.ones((N,1))])
                world_pts = (T_world @ (S @ hom.T)).T[:,:3]
                combined_vertices.extend(world_pts.tolist())
                skeleton_vertices_count += N

                # faces (with proper indexing validation)
                faces = []
                idx = 0
                for cnt in seg["faceCounts"]:
                    if idx + cnt <= len(seg["faceIndices"]):
                        face = seg["faceIndices"][idx: idx+cnt]
                        if len(face) >= 3:  # Valid face
                            adjusted_face = [v + vertex_offset for v in face if v + vertex_offset < len(combined_vertices) + N]
                            if len(adjusted_face) >= 3:
                                faces.append(adjusted_face)
                        idx += cnt
                    else:
                        print(f"WARNING: Face index out of bounds for {bname}")
                        break
                combined_faces.extend(faces)
                vertex_offset += N

            # **IMU box**
            if bname in imu_offsets:
                imuVerts, imuFaces = create_imu_box_with_rotation(
                    T_world, imu_offsets[bname], imu_extents,
                    rotateDeg=(45 if "calcn" in bname else 0),
                    rotateAxis=np.array([0,0,1])
                )
                combined_vertices.extend(imuVerts.tolist())
                combined_faces.extend([[v + vertex_offset for v in face] for face in imuFaces])
                vertex_offset += imuVerts.shape[0]
                imu_vertices_count += imuVerts.shape[0]
        
        pct = int(100 * (i + 1) / len(frame_indices))
        print(f"PROGRESS {pct}", flush=True)
        
        # Debug info for geometry
        print(f"DEBUG Frame {fIdx}: Skeleton vertices: {skeleton_vertices_count}, IMU vertices: {imu_vertices_count}")
        print(f"DEBUG Frame {fIdx}: Total vertices: {len(combined_vertices)}, Total faces: {len(combined_faces)}")
        
        # write OBJ
        write_obj_file(
            os.path.join(outputFolder, f"frame_{fIdx:04d}.obj"),
            combined_vertices, combined_faces)

        # render to image
        img = render_combined_frame(combined_vertices, combined_faces,
                                    camera, cam_pose, resolution)
        frames.append(img)

    return frames 
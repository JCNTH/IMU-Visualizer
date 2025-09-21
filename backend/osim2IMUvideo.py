#!/usr/bin/env python3
"""
osim2IMUvideo.py

This script:
  1. Reads an OpenSim model (.osim) and a motion file (.mot), uses a mot2quats routine to compute per‐frame body poses,
     and renders each frame using the attached mesh geometry plus small IMU boxes on each body segment.
  2. The final frames are assembled into a video with a white background.
  3. Additionally, for each frame an OBJ file (combining skeleton and IMU geometry) is saved to an output folder.

A calibration file (calib.npz) must contain:
    - K: camera intrinsics (3x3 matrix)
    - R: camera-to-world rotation (3x3 matrix)
    - T: camera-to-world translation (3-element vector)

Usage:
    python osim2IMUvideo.py -i <model.osim> -m <motion.mot> -c <calib.npz> -o <outputVideo.mp4>

    Example:
    python osim2IMUvideo.py -i Motions/subject22/scaled_model.osim -m Motions/subject6/ik2.mot -c Motions/subject6/calib.npz -o video.mp4
"""

import os, sys, math, getopt, io
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
import sys

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
    lines = []
    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    for face in faces:
        lines.append("f " + " ".join(str(i+1) for i in face))
    obj_data = "\n".join(lines)
    obj_file = io.StringIO(obj_data)
    mesh = trimesh.load(obj_file, file_type='obj')
    return mesh

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
        # Create a trimesh from the combined geometry
        mesh = mesh_from_memory(combined_vertices, combined_faces)

        # (Color logic omitted from final script for simplicity)
        # If you want to color the IMUs red, reintroduce face-colors here.

        # Horizontally center the mesh (X, Z) only
        min_bounds = mesh.bounds[0]
        max_bounds = mesh.bounds[1]
        center_x = (min_bounds[0] + max_bounds[0]) / 2.0
        center_z = (min_bounds[2] + max_bounds[2]) / 2.0
        translation = np.array([-center_x, 0, -center_z])
        mesh.apply_translation(translation)
        
        # Convert to pyrender mesh
        pyr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=True)
        
        # Create scene with white background
        scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0])
        scene.add(pyr_mesh)
        scene.add(camera, pose=cam_pose)
        
        # Add a directional light
        light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=5.0)
        scene.add(light, pose=cam_pose)
        
        # Render the scene
        renderer = pyrender.OffscreenRenderer(viewport_width=resolution[0], viewport_height=resolution[1])
        color, depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        renderer.delete()
        
        return color
    except Exception as e:
        print(f"Rendering error: {e}")
        return np.ones((resolution[1], resolution[0], 4), dtype=np.uint8) * 255  # White image

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
            sys.exit(-1)
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
def export_obj_frames_withIMU(osimPath, geomPath, motionPath,
                              outputFolder, optionsDict, calib_path):
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
    # ---------------

    from tqdm import tqdm
    # 2) SET UP CAMERA
    print(f"Loading calibration: {calib_path}")
    K = np.load(calib_path)["K"]
    camera = create_camera(K)
    cam_pose = np.eye(4); cam_pose[:3,3] = [0,0,2.5]
    resolution = (1920,1080)

    # 3) LOAD MOTION TRAJECTORY
    _, (bodyNames, times, poseTrajectories) = mot2quats(
        motionPath, osimPath, {}, optionsDict)
    nFrames = len(times)
    print(f"Total frames: {nFrames}")

    # 4) EXPORT + RENDER WITH PROGRESS BAR
    frames = []
    for fIdx in tqdm(range(nFrames), desc="Rendering frames"):
        tVal = times[fIdx]
        framePoses = poseTrajectories[fIdx]

        combined_vertices = []
        combined_faces = []
        vertex_offset = 0

        # build skeleton + IMU geometry for this frame
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

                # faces
                faces = []
                idx = 0
                for cnt in seg["faceCounts"]:
                    face = seg["faceIndices"][idx: idx+cnt]
                    faces.append([v + vertex_offset for v in face])
                    idx += cnt
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
        
        pct = int(100 * (fIdx + 1) / nFrames)
        print(f"PROGRESS {pct}", flush=True)
        # write OBJ
        write_obj_file(
            os.path.join(outputFolder, f"frame_{fIdx:04d}.obj"),
            combined_vertices, combined_faces)

        # render to image
        img = render_combined_frame(combined_vertices, combined_faces,
                                    camera, cam_pose, resolution)
        frames.append(img)

        # **simple memory trim every 50 frames**
        # if fIdx % 50 == 0:
        #     gc.collect()

    return frames

##############################
# Main
##############################
def main(argv):
    print("OpenSim to IMU Video conversion (no background overlay)")
    optionsDict = {}
    optionsDict["outputFolder"] = "./imu"
    
    # columns in degrees
    optionsDict["columnsInDegrees"] = [
        "pelvis_tilt", "pelvis_list", "pelvis_rotation", "pelvis_tx", "pelvis_ty", "pelvis_tz", 
        "hip_flexion_r", "hip_adduction_r", "hip_rotation_r",
        "knee_angle_r", "knee_angle_r_beta", "ankle_angle_r", "subtalar_angle_r", "mtp_angle_r",
        "hip_flexion_l", "hip_adduction_l", "hip_rotation_l",
        "knee_angle_l", "knee_angle_l_beta", "ankle_angle_l", "subtalar_angle_l", "mtp_angle_l",
        "lumbar_extension", "lumbar_bending", "lumbar_rotation",
        "knee_adduction_l", "knee_rotation_l", "ankle_adduction_l", "ankle_rotation_l",
        "knee_adduction_r", "knee_rotation_r", "ankle_adduction_r", "ankle_rotation_r"
    ]
    optionsDict["motionFormat"] = "localRotationsOnly"
    optionsDict["activationSTO"] = False

    osimPath = ""
    motPath = ""
    calibPath = ""
    outVideoPath = ""
    import getopt
    opts, args = getopt.getopt(argv, "hi:m:c:o:", ["input=", "motion=", "calib=", "output="])
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("Usage: python osim2IMUvideo.py -i <model.osim> -m <motion.mot> -c <calib.npz> -o <outVideo.mp4>")
            sys.exit()
        elif opt in ("-i", "--input"):
            osimPath = arg
        elif opt in ("-m", "--motion"):
            motPath = arg
        elif opt in ("-c", "--calib"):
            calibPath = arg
        elif opt in ("-o", "--output"):
            outVideoPath = arg

    if not osimPath or not motPath or not calibPath or not outVideoPath:
        print("Error: Must provide -i <model.osim>, -m <motion.mot>, -c <calib.npz>, -o <outVideo.mp4>")
        sys.exit(-1)

    if not os.path.exists(optionsDict["outputFolder"]):
        os.makedirs(optionsDict["outputFolder"], exist_ok=True)

    frames = export_obj_frames_withIMU(osimPath, "./Model/Geometry", motPath,
                                       optionsDict["outputFolder"], optionsDict, calibPath)
    if not frames:
        print("No frames rendered. Exiting.")
        sys.exit(-1)

    if os.path.isabs(outVideoPath):
        videoPath = outVideoPath
    else:
        videoPath = os.path.join(optionsDict["outputFolder"], outVideoPath)
    fps = 30
    print(f"Writing final video to: {videoPath} at {fps} fps")
    import imageio
    imageio.mimwrite(videoPath, frames, fps=fps)
    print("Done. Final video saved to:", videoPath)
    print("VIDEO_READY", flush=True)
    sys.exit(0)          # optional but explicit

if __name__ == "__main__":
    main(sys.argv[1:])
 


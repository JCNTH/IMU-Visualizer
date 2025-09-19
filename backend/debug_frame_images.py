#!/usr/bin/env python3
"""Debug script to save individual rendered frames as images"""

import os
import sys
from pathlib import Path
import numpy as np
import imageio

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.osim2video_imu import (
    export_obj_frames_withIMU, 
    render_combined_frame, 
    create_camera,
    mot2quats
)
import xml.etree.ElementTree as ET

def debug_frame_images():
    """Generate individual frame images to debug rendering"""
    
    print("🔍 DEBUG: Saving individual frame images...")
    
    # Use the working model and paths
    model_path = "Model/LaiArnoldModified2017_poly_withArms_weldHand_scaled_adjusted.osim"
    motion_path = "static/sessions/session_ik.mot"
    calib_path = "static/models/default_calib.npz"
    geometry_path = "./Model/Geometry"
    output_dir = "static/sessions/debug_frames"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Load calibration and setup camera
        K = np.load(calib_path)["K"]
        camera = create_camera(K)
        cam_pose = np.eye(4)
        cam_pose[:3, 3] = [0, 1, 2]
        resolution = (480, 270)
        
        print(f"Camera matrix K: {K}")
        print(f"Camera pose: {cam_pose}")
        print(f"Resolution: {resolution}")
        
        # Parse model for geometry (minimal version)
        tree = ET.parse(model_path)
        root = tree.getroot()
        bodySet = root.find("./Model/BodySet")
        base_body_geometry = {}
        
        print("Loading geometry...")
        geometry_count = 0
        for bodyElem in bodySet.findall("./objects/Body"):
            bname = bodyElem.get("name")
            meshes = []
            for meshElem in bodyElem.findall("./attached_geometry/Mesh"):
                meshFile = os.path.join(geometry_path, meshElem.find("mesh_file").text.strip())
                scales = [float(x) for x in meshElem.findtext("scale_factors", "1 1 1").split()]
                try:
                    from utils.osim2video_imu import get_vtp_mesh_arrays
                    fcCounts, fcIndices, pts_local = get_vtp_mesh_arrays(meshFile)
                    meshes.append({
                        "pts_local": pts_local,
                        "scales": scales,
                        "faceCounts": fcCounts,
                        "faceIndices": fcIndices
                    })
                    geometry_count += 1
                except Exception as e:
                    print(f"Failed to load {meshFile}: {e}")
            if meshes:
                base_body_geometry[bname] = meshes
        
        print(f"Loaded {geometry_count} geometry pieces for {len(base_body_geometry)} bodies")
        
        # Load motion data
        optionsDict = {
            "columnsInDegrees": [
                "pelvis_tilt", "pelvis_list", "pelvis_rotation", "pelvis_tx", "pelvis_ty", "pelvis_tz", 
                "hip_flexion_r", "hip_adduction_r", "hip_rotation_r",
                "knee_angle_r", "knee_angle_r_beta", "ankle_angle_r", "subtalar_angle_r", "mtp_angle_r",
                "hip_flexion_l", "hip_adduction_l", "hip_rotation_l",
                "knee_angle_l", "knee_angle_l_beta", "ankle_angle_l", "subtalar_angle_l", "mtp_angle_l",
                "lumbar_extension", "lumbar_bending", "lumbar_rotation"
            ]
        }
        
        result = mot2quats(motion_path, model_path, {}, optionsDict)
        if result is None:
            print("❌ Failed to load motion data")
            return False
            
        _, (bodyNames, times, poseTrajectories) = result
        print(f"Motion loaded: {len(bodyNames)} bodies, {len(times)} frames")
        
        # Test first few frames
        test_frames = min(3, len(times))
        
        for fIdx in range(test_frames):
            print(f"\n--- Testing Frame {fIdx} ---")
            
            tVal = times[fIdx]
            framePoses = poseTrajectories[fIdx]
            
            combined_vertices = []
            combined_faces = []
            vertex_offset = 0
            
            # Build geometry for this frame
            for bname, meshes in base_body_geometry.items():
                if bname not in bodyNames:
                    continue
                iB = bodyNames.index(bname)
                pos, quat = framePoses[iB]
                
                from utils.osim2video_imu import pose_to_matrix
                T_world = pose_to_matrix(pos, quat)
                
                # Add skeleton geometry
                for seg in meshes:
                    pts = seg["pts_local"]
                    scales = seg["scales"]
                    N = pts.shape[0]
                    S = np.diag(scales + [1])
                    hom = np.hstack([pts, np.ones((N,1))])
                    world_pts = (T_world @ (S @ hom.T)).T[:,:3]
                    combined_vertices.extend(world_pts.tolist())
                    
                    # Add faces
                    faces = []
                    idx = 0
                    for cnt in seg["faceCounts"]:
                        face = seg["faceIndices"][idx: idx+cnt]
                        faces.append([v + vertex_offset for v in face])
                        idx += cnt
                    combined_faces.extend(faces)
                    vertex_offset += N
            
            print(f"Frame {fIdx}: {len(combined_vertices)} vertices, {len(combined_faces)} faces")
            
            if len(combined_vertices) == 0:
                print(f"❌ Frame {fIdx}: No geometry data!")
                continue
                
            # Render the frame
            img = render_combined_frame(combined_vertices, combined_faces, camera, cam_pose, resolution)
            
            if img is None:
                print(f"❌ Frame {fIdx}: Rendering failed!")
                continue
                
            # Save as PNG
            png_path = f"{output_dir}/frame_{fIdx:03d}.png"
            imageio.imwrite(png_path, img)
            print(f"✅ Saved: {png_path}")
            
            # Analyze the image
            if len(img.shape) == 3 and img.shape[2] == 4:  # RGBA
                alpha_pixels = np.sum(img[:,:,3] > 0)
                non_transparent = np.sum(img[:,:,3] > 128)
                print(f"   Image analysis: {img.shape}, alpha pixels: {alpha_pixels}, solid pixels: {non_transparent}")
            else:
                non_zero = np.sum(img > 0)
                print(f"   Image analysis: {img.shape}, non-zero pixels: {non_zero}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_frame_images()
    if success:
        print("\n✅ Frame images saved successfully!")
        print("🎯 Check the PNG files in static/sessions/debug_frames/")
        print("💡 Compare with OBJ files to see if rendering is working")
    else:
        print("\n❌ Frame image debug failed!")
        print("🔧 Check the error messages above") 
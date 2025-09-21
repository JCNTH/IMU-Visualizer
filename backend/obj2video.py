#!/usr/bin/env python3
"""
obj2video.py

Render a sequence of OBJ files (from a folder) using camera intrinsics from a calibration file.
Instead of using the calibration’s extrinsics, this script centers each mesh and uses a fixed camera pose.
The resulting frames are assembled into a video.
 
Usage:
    python obj2video.py --obj <obj_folder> --calib <calib.npz> --output <output_video.mp4> [--width WIDTH] [--height HEIGHT] [--fps FPS]
"""

import os
import glob
import argparse
import numpy as np
import trimesh
import pyrender
import imageio

def load_calibration(calib_path):
    """
    Load calibration data from a .npz file.
    We only use K (intrinsics) in this script.
    """
    calib = np.load(calib_path, allow_pickle=True)
    K = calib["K"]
    return K

def create_camera(K, znear=0.1, zfar=1000.0):
    """
    Create a pyrender.IntrinsicsCamera using the intrinsics from K.
    K is a 3x3 matrix:
        [ [fx,  0, cx],
          [ 0, fy, cy],
          [ 0,  0,  1] ]
    """
    fx = K[0, 0]
    fy = K[1, 1]
    cx = K[0, 2]
    cy = K[1, 2]
    camera = pyrender.IntrinsicsCamera(fx=fx, fy=fy, cx=cx, cy=cy, znear=znear, zfar=zfar)
    return camera

def render_obj_frame(obj_path, camera, cam_pose, resolution):
    """
    Load an OBJ file, center the mesh by aligning its bottom to y=0 and its horizontal center to (0,0),
    add it to a pyrender scene along with the given camera and a directional light,
    render the scene offscreen, and return the resulting image.
    """
    # Load the mesh (forcing a mesh)
    mesh = trimesh.load(obj_path, force='mesh')

    for face in mesh.faces:
        if len(face) > 3:
            print(face)




    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"File {obj_path} did not load as a trimesh.Trimesh object.")
    
    # Instead of subtracting the centroid, use the bounding box to:
    #   - move the minimum y (e.g. feet) to y=0,
    #   - and center the mesh horizontally in X and Z.
    min_bounds = mesh.bounds[0]  # [min_x, min_y, min_z]
    max_bounds = mesh.bounds[1]  # [max_x, max_y, max_z]
    center_x = (min_bounds[0] + max_bounds[0]) / 2.0
    center_z = (min_bounds[2] + max_bounds[2]) / 2.0
    translation = np.array([-center_x, -min_bounds[1], -center_z])
    mesh.apply_translation(translation)
    
    # Convert the transformed trimesh to a pyrender mesh.
    pyr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=True)
    
    # Create a new scene with a light gray background (so a light-colored mesh is visible).
    scene = pyrender.Scene(bg_color=[0.8, 0.8, 0.8, 1.0])
    scene.add(pyr_mesh)
    scene.add(camera, pose=cam_pose)
    
    # Add a directional light. (You can adjust its intensity and pose if needed.)
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
    # For simplicity, we add the light at the same pose as the camera.
    scene.add(light, pose=cam_pose)
    
    # Create an offscreen renderer.
    renderer = pyrender.OffscreenRenderer(viewport_width=resolution[0], viewport_height=resolution[1])
    color, depth = renderer.render(scene)
    renderer.delete()
    return color


def parse_args():
    parser = argparse.ArgumentParser(description="Render OBJ files with calibrated intrinsics and a fixed camera pose; output a video.")
    parser.add_argument("--obj", required=True, help="Path to folder containing OBJ files.")
    parser.add_argument("--calib", required=True, help="Path to calibration file (.npz) containing K.")
    parser.add_argument("--output", required=True, help="Output video filename (e.g. output.mp4).")
    parser.add_argument("--width", type=int, default=2560, help="Video frame width in pixels.")
    parser.add_argument("--height", type=int, default=1440, help="Video frame height in pixels.")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for output video.")
    return parser.parse_args()

def main():
    args = parse_args()
    obj_dir = args.obj
    calib_path = args.calib
    output_video = args.output
    resolution = (args.width, args.height)
    fps = args.fps

    # Load the calibration intrinsics
    K = load_calibration(calib_path)
    camera = create_camera(K)
    
    # For this rendering, we ignore the calibration extrinsics and use a default camera pose.
    # For example, place the camera at [0, 0, 2] looking at the origin.
    cam_pose = np.eye(4)
    cam_pose[:3, 3] = [0, 1, 2]
    
    print("Using camera intrinsics from calibration and a default camera pose:")
    print("K:\n", K)
    print("Camera pose (camera-to-world):\n", cam_pose)
    
    # Get sorted list of OBJ files from the provided folder.
    obj_files = sorted(glob.glob(os.path.join(obj_dir, "*.obj")))
    if not obj_files:
        print(f"No OBJ files found in {obj_dir}")
        return

    frames = []
    num_frames = len(obj_files)
    print(f"Found {num_frames} OBJ files. Rendering video...")
    for i, obj_file in enumerate(obj_files):
        print(f"Rendering frame {i+1}/{num_frames} from {obj_file}")
        try:
            img = render_obj_frame(obj_file, camera, cam_pose, resolution)
            frames.append(img)
        except Exception as e:
            print(f"Rendering failed for {obj_file}: {e}")

    if not frames:
        print("No frames rendered. Exiting.")
        return

    print(f"Writing video to {output_video} at {fps} fps...")
    imageio.mimwrite(output_video, frames, fps=fps)
    print(f"Video saved to: {output_video}")

if __name__ == "__main__":
    main()
